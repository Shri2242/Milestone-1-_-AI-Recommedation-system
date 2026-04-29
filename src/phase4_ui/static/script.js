document.addEventListener('DOMContentLoaded', () => {
    
    // Rating Slider logic
    const ratingSlider = document.getElementById('min_rating');
    const ratingVal = document.getElementById('rating_val');
    
    if (ratingSlider && ratingVal) {
        ratingSlider.addEventListener('input', (e) => {
            ratingVal.textContent = e.target.value;
        });
    }

    // Submit loading state
    const form = document.getElementById('recommendation-form');
    const submitBtn = document.getElementById('submit-btn');

    if (form && submitBtn) {
        form.addEventListener('submit', (e) => {
            // Check if at least one field has value
            const formData = new FormData(form);
            const location = formData.get('location');
            const budget = formData.get('budget');
            const cuisine = formData.get('cuisine');
            const rating = formData.get('min_rating');
            const additional = formData.get('additional_prefs');
            
            const hasInput = location || budget || cuisine || rating !== '0' || additional;
            
            if (hasInput) {
                // Show loading state
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Allow form to submit naturally
            }
        });
    }
});
