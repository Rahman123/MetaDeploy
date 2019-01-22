from unittest.mock import MagicMock, sentinel

import pytest
from django.core.cache import cache

from ..constants import REDIS_JOB_CANCEL_KEY
from ..flows import (
    BasicFlowCallback,
    JobFlowCallback,
    PreflightFlowCallback,
    StopFlowException,
)
from ..models import Step


def test_get_step_id(mocker):
    basic_flow = BasicFlowCallback(sentinel.result)
    basic_flow._steps = Step.objects.none()
    result = basic_flow._get_step_id("anything")

    assert result is None


class TestJobFlow:
    def test_init(self, mocker):
        flow = JobFlowCallback(sentinel.job)
        assert flow.context == sentinel.job

    @pytest.mark.django_db
    def test_cancel_job(self, mocker, job_factory):
        job = job_factory()
        flow = JobFlowCallback(job)
        cache.set(REDIS_JOB_CANCEL_KEY.format(id=job.id), True)
        with pytest.raises(StopFlowException):
            flow.pre_task(None)

    @pytest.mark.django_db
    def test_post_task(
        self, mocker, user_factory, plan_factory, step_factory, job_factory
    ):
        plan = plan_factory()
        steps = [step_factory(plan=plan, path=f"task_{i}") for i in range(3)]

        job = job_factory(plan=plan, steps=steps)

        flow = JobFlowCallback(job)

        tasks = [MagicMock() for _ in range(3)]
        for i, task in enumerate(tasks):
            task.name = f"task_{i}"

        flow._init_logger()
        for task in tasks:
            flow.post_task(task, sentinel.task_result)
        flow.post_flow()

        assert job.results == {str(step.id): [{"status": "ok"}] for step in steps}

    @pytest.mark.django_db
    def test_post_task_exception(
        self, mocker, user_factory, plan_factory, step_factory, job_factory
    ):
        user = user_factory()
        plan = plan_factory()
        steps = [step_factory(plan=plan, path=f"task_{i}") for i in range(3)]

        job = job_factory(user=user, plan=plan, steps=steps)

        flow = JobFlowCallback(job)

        task = MagicMock()
        task.name = f"task_0"

        flow._init_logger()
        flow._post_task_exception(task, ValueError("Some error"))

        assert job.results == {
            str(steps[0].id): [{"status": "error", "message": "Some error"}]
        }


class TestPreflightFlow:
    def test_init(self, mocker):
        preflight_flow = PreflightFlowCallback(sentinel.preflight)
        assert preflight_flow.context == sentinel.preflight

    @pytest.mark.django_db
    def test_post_flow(
        self, mocker, user_factory, plan_factory, step_factory, preflight_result_factory
    ):
        user = user_factory()
        plan = plan_factory()
        step1 = step_factory(plan=plan, path="name_1")
        step_factory(plan=plan, path="name_2")
        step3 = step_factory(plan=plan, path="name_3")
        step4 = step_factory(plan=plan, path="name_4")
        step5 = step_factory(plan=plan, path="name_5")
        pfr = preflight_result_factory(user=user, plan=plan)
        preflight_flow = PreflightFlowCallback(pfr)
        preflight_flow.step_return_values = [
            {"path": "name_1", "status_code": "error", "msg": "error 1"},
            {"path": "name_2", "status_code": "ok"},
            {"path": "name_3", "status_code": "warn", "msg": "warn 1"},
            {"path": "name_4", "status_code": "optional"},
            {"path": "name_5", "status_code": "skip", "msg": "skip 1"},
        ]

        preflight_flow.post_flow()

        assert pfr.results == {
            step1.id: [{"status": "error", "message": "error 1"}],
            step3.id: [{"status": "warn", "message": "warn 1"}],
            step4.id: [{"status": "optional", "message": ""}],
            step5.id: [{"status": "skip", "message": "skip 1"}],
        }

    @pytest.mark.django_db
    def test_post_task_exception(
        self, mocker, user_factory, plan_factory, preflight_result_factory
    ):
        user = user_factory()
        plan = plan_factory()
        pfr = preflight_result_factory(user=user, plan=plan)
        preflight_flow = PreflightFlowCallback(pfr)

        exc = ValueError("A value error.")
        preflight_flow._post_task_exception(None, exc)

        assert pfr.results == {
            "plan": [{"status": "error", "message": "A value error."}]
        }
