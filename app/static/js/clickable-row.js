document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('.clickable-row');

    rows.forEach(row => {
        row.addEventListener('click', function(event) {
            if (event.target.closest('a, button, input, select, textarea')) {
                return;
            }

            const href = this.dataset.href;
            if (href) {
               if (event.ctrlKey || event.metaKey || event.which === 2) {
                   window.open(href, '_blank');
               } else {
                   window.location.href = href;
               }
            }
        });
    });
});