// @flow

import * as React from 'react';
import Button from '@salesforce/design-system-react/components/button';
import Checkbox from '@salesforce/design-system-react/components/checkbox';
import Modal from '@salesforce/design-system-react/components/modal';
import i18n from 'i18next';

import { CONSTANTS } from 'store/plans/reducer';
import { WarningIcon } from 'components/plans/preflightResults';
import type {
  PreflightErrors as PreflightErrorsType,
  StepResult as StepResultType,
  Step as StepType,
} from 'store/plans/reducer';
import type { SelectedSteps as SelectedStepsType } from 'components/plans/detail';

type Props = {
  isOpen: boolean,
  toggleModal: (boolean) => void,
  startJob: () => void,
  results: PreflightErrorsType,
  steps: Array<StepType>,
  selectedSteps: SelectedStepsType,
};
type State = {
  confirmed: boolean,
};

const Warning = ({
  id,
  result,
  name,
}: {
  id: string,
  result: StepResultType,
  name?: string,
}): React.Node => {
  if (result.message && result.status === CONSTANTS.RESULT_STATUS.WARN) {
    return (
      <div className="slds-p-vertical_x-small">
        {name && id !== 'plan' ? (
          <h2
            className="slds-text-heading_small
              slds-p-bottom_x-small"
          >
            {name}
          </h2>
        ) : null}
        <ul>
          <li>
            <WarningIcon />
            {/* These messages are pre-cleaned by the API */}
            <span dangerouslySetInnerHTML={{ __html: result.message }} />
          </li>
        </ul>
      </div>
    );
  }
  return null;
};

class PreflightWarningModal extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { confirmed: false };
  }

  handleClose = () => {
    this.setState({ confirmed: false });
    this.props.toggleModal(false);
  };

  handleSubmit = () => {
    const { startJob } = this.props;
    this.handleClose();
    startJob();
  };

  handleChange = (
    event: SyntheticInputEvent<HTMLInputElement>,
    { checked }: { checked: boolean },
  ) => {
    this.setState({ confirmed: checked });
  };

  render(): React.Node {
    const { isOpen, results, steps, selectedSteps } = this.props;
    const { confirmed } = this.state;
    const footer = [
      <Button
        key="cancel"
        label={i18n.t('Cancel')}
        onClick={this.handleClose}
      />,
      <Button
        key="submit"
        label={i18n.t('Confirm')}
        variant="brand"
        onClick={this.handleSubmit}
        disabled={!confirmed}
      />,
    ];
    return (
      <Modal
        isOpen={isOpen}
        heading={i18n.t('Potential Issues')}
        tagline={i18n.t('(confirm to continue)')}
        onRequestClose={this.handleClose}
        footer={footer}
      >
        <div className="slds-p-horizontal_large slds-p-vertical_medium">
          {results.plan ? <Warning id="plan" result={results.plan} /> : null}
          {[...selectedSteps].map((id) => {
            const step = steps.find((s) => s.id === id);
            const stepResult = results[id];
            if (!step || !stepResult) {
              return null;
            }
            return (
              <Warning key={id} id={id} result={stepResult} name={step.name} />
            );
          })}
          <Checkbox
            id="preflight-warning-confirm"
            className="slds-p-top_x-small"
            checked={this.state.confirmed}
            labels={{
              label: i18n.t(
                'I understand these warnings, and want to continue with installation.',
              ),
            }}
            onChange={this.handleChange}
          />
        </div>
      </Modal>
    );
  }
}

export default PreflightWarningModal;
