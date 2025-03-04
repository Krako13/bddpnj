document.addEventListener('DOMContentLoaded', function() {
    // Placez ici l'intégralité de votre code de pnjlaelith.js

    // Exemple de code :
    var lieuFilter = document.getElementById('lieuFilter');
    if (lieuFilter) {
        lieuFilter.addEventListener('change', function() {
            // Réinitialiser la page à 1 et soumettre le formulaire
            var pageInput = document.querySelector('input[name="page"]');
            if (pageInput) pageInput.value = 1;
            document.getElementById('search-form').submit();
        });
    } else {
        console.error("Element avec id 'lieuFilter' non trouvé.");
    }

    // Continuez avec le reste de votre code pnjlaelith.js
    document.getElementById('searchInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            var pageInput = document.querySelector('input[name="page"]');
            if (pageInput) pageInput.value = 1;
            document.getElementById('search-form').submit();
        }
    });

    document.getElementById('search-icon').addEventListener('click', function() {
        var pageInput = document.querySelector('input[name="page"]');
        if (pageInput) pageInput.value = 1;
        document.getElementById('search-form').submit();
    });

    document.getElementById('reset-btn').addEventListener('click', function() {
        document.getElementById('lieuFilter').value = '';
        document.getElementById('searchInput').value = '';
        var pageInput = document.querySelector('input[name="page"]');
        if (pageInput) pageInput.value = 1;
        document.getElementById('search-form').submit();
    });
});
