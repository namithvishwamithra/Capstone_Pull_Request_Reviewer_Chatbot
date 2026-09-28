interface PrivacyConsentProps {
  accepted: boolean;
  onChange: (accepted: boolean) => void;
}

export function PrivacyConsent({ accepted, onChange }: PrivacyConsentProps) {
  return (
    <label className="consent-card">
      <input
        type="checkbox"
        checked={accepted}
        onChange={(event) => onChange(event.target.checked)}
        aria-describedby="privacy-copy"
      />
      <span>
        <strong>Privacy notice</strong>
        <span id="privacy-copy">
          Your submitted code will be sent to Google AI Studio for review. It
          will not be saved beyond this active session unless you explicitly
          save the review.
        </span>
      </span>
    </label>
  );
}
