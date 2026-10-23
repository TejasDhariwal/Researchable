document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("questionnaire-form");
    if (!form) {
        return;
    }

    const steps = Array.from(form.querySelectorAll(".question-step"));
    const previousButton = document.getElementById("previous-button");
    const nextButton = document.getElementById("next-button");
    const submitButton = document.getElementById("submit-button");
    const stepError = document.getElementById("step-error");
    const progressFill = document.getElementById("progress-fill");
    const progressTrack = document.getElementById("progress-track");
    const progressPercent = document.getElementById("progress-percent");
    const progressStep = document.getElementById("progress-step");
    const progressMessage = document.getElementById("progress-message");
    const messages = [
        "Let's start with your idea.",
        "Nice start — let's shape the direction.",
        "We got it — defining your sources.",
        "Almost there — choosing your deliverables.",
        "Final details — you're nearly done.",
    ];
    let activeStep = 0;

    function updateConditionalInputs() {
        form.querySelectorAll("[data-other-toggle]").forEach((control) => {
            const target = document.getElementById(control.dataset.otherToggle);
            if (!target) {
                return;
            }

            const selected = control.type === "radio"
                ? control.checked
                : form.querySelector(`[name="${control.name}"][value="${control.value}"]`).checked;
            target.hidden = !selected;
        });
    }

    function updateView() {
        steps.forEach((step, index) => {
            const isActive = index === activeStep;
            step.hidden = !isActive;
            step.classList.toggle("is-active", isActive);
        });
        previousButton.hidden = activeStep === 0;
        nextButton.hidden = activeStep === steps.length - 1;
        submitButton.hidden = activeStep !== steps.length - 1;

        const progress = activeStep * 20;
        progressFill.style.width = `${progress}%`;
        progressTrack.setAttribute("aria-valuenow", String(progress));
        progressPercent.textContent = `${progress}%`;
        progressStep.textContent = `Questions ${activeStep * 2 + 1}–${activeStep * 2 + 2} of 10`;
        progressMessage.textContent = messages[activeStep];
        stepError.hidden = true;
    }

    function validateActiveStep() {
        updateConditionalInputs();
        const activePane = steps[activeStep];
        const requiredFields = Array.from(activePane.querySelectorAll("[data-required], [data-required-when]"))
            .filter((field) => !field.hidden);

        for (const field of requiredFields) {
            if (field.type === "radio") {
                const selected = activePane.querySelector(`input[name="${field.name}"]:checked`);
                if (!selected) {
                    field.focus();
                    showError("Please choose an option before continuing.");
                    return false;
                }
            } else if (!field.value.trim()) {
                field.focus();
                showError("Please complete the required fields before continuing.");
                return false;
            }
        }

        for (const name of ["audience", "critical_analysis", "report_word_count", "slide_count"]) {
            const group = activePane.querySelector(`input[type="radio"][name="${name}"]`);
            if (group && !activePane.querySelector(`input[type="radio"][name="${name}"]:checked`)) {
                group.focus();
                showError("Please choose an option before continuing.");
                return false;
            }
        }

        for (const name of ["scope", "evidence", "outputs"]) {
            const group = activePane.querySelector(`input[type="checkbox"][name="${name}"]`);
            if (group && !activePane.querySelector(`input[type="checkbox"][name="${name}"]:checked`)) {
                group.focus();
                showError("Please select at least one option in each question.");
                return false;
            }
        }

        showError("");
        return true;
    }

    function showError(message) {
        stepError.textContent = message;
        stepError.hidden = !message;
    }

    form.addEventListener("change", updateConditionalInputs);
    nextButton.addEventListener("click", () => {
        if (validateActiveStep()) {
            activeStep += 1;
            updateView();
        }
    });
    previousButton.addEventListener("click", () => {
        activeStep -= 1;
        updateView();
    });
    form.addEventListener("submit", (event) => {
        if (!validateActiveStep()) {
            event.preventDefault();
        }
    });

    updateConditionalInputs();
    updateView();
});
