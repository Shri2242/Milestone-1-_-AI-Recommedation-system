/* ======================================================
   Client-side JavaScript
   ====================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // --- Rating slider live value ---
    const slider = document.getElementById("min_rating");
    const ratingValue = document.getElementById("rating-value");

    if (slider && ratingValue) {
        const updateRating = () => {
            const val = parseFloat(slider.value);
            ratingValue.textContent = val === 0 ? "Any" : `${val.toFixed(1)} ⭐`;
        };
        slider.addEventListener("input", updateRating);
        updateRating();
    }

    // --- Flash message auto-dismiss ---
    const flashMessages = document.querySelectorAll(".flash");
    flashMessages.forEach((msg) => {
        setTimeout(() => {
            msg.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            msg.style.opacity = "0";
            msg.style.transform = "translateY(-10px)";
            setTimeout(() => msg.remove(), 400);
        }, 5000);
    });

    // --- Form validation before submit ---
    const form = document.getElementById("preferences-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            const location = document.getElementById("location").value.trim();
            const cuisine = document.getElementById("cuisine").value.trim();
            const budget = document.getElementById("budget").value;
            const rating = parseFloat(document.getElementById("min_rating").value);
            const additional = document.getElementById("additional_prefs").value.trim();

            const hasInput = location || cuisine || budget || rating > 0 || additional;

            if (!hasInput) {
                e.preventDefault();
                showFlash("Please fill in at least one preference.", "warning");
                return;
            }

            // Show loading state on button
            const btn = form.querySelector(".btn--primary");
            if (btn) {
                btn.innerHTML = '<span class="spinner"></span> Finding restaurants...';
                btn.disabled = true;
                btn.style.opacity = "0.7";
            }
        });
    }
});

/**
 * Show a temporary flash message
 */
function showFlash(message, type = "warning") {
    const container = document.querySelector(".flash-messages") || createFlashContainer();
    const flash = document.createElement("div");
    flash.className = `flash flash--${type}`;
    flash.textContent = message;
    container.appendChild(flash);

    setTimeout(() => {
        flash.style.transition = "opacity 0.4s ease";
        flash.style.opacity = "0";
        setTimeout(() => flash.remove(), 400);
    }, 4000);
}

function createFlashContainer() {
    const container = document.createElement("div");
    container.className = "flash-messages";
    const card = document.querySelector(".card") || document.querySelector(".container");
    if (card) {
        card.insertBefore(container, card.firstChild);
    }
    return container;
}
