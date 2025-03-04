
const categoryDescriptions = {
    "Taverne": "PNJ que l'on peut rencontrer dans des tavernes, où les aventuriers se retrouvent pour boire, échanger des histoires, et parfois trouver du travail. Les tavernes sont souvent des lieux animés où les informations circulent librement.",
    "Lieu Malfamé": "PNJ que l'on peut rencontrer dans des lieux dangereux ou illégaux, souvent impliqués dans des activités criminelles. Ces endroits sont fréquentés par des individus louches et des hors-la-loi.",
    "Forêt/Nature": "PNJ que l'on peut rencontrer dans des environnements naturels, comme les forêts ou les montagnes. Ces personnages sont souvent des chasseurs, des ermites, ou des créatures sauvages.",
    "Marché": "PNJ que l'on peut rencontrer dans des lieux publics, comme les marchés ou les places de village. Ces endroits sont propices aux rencontres et aux échanges commerciaux.",
    "Bibliothèque Ancienne": "PNJ que l'on peut rencontrer dans des lieux de savoir ancien, comme les bibliothèques ou les archives. Ces personnages sont souvent des érudits ou des gardiens de connaissances oubliées.",
    "Château/Palais": "PNJ que l'on peut rencontrer dans des lieux de pouvoir, comme les châteaux ou les palais. Ces personnages sont souvent des nobles, des conseillers, ou des gardes royaux.",
    "Guilde/Atelier": "PNJ que l'on peut rencontrer dans des lieux de travail, comme les guildes ou les ateliers d'artisans. Ces personnages sont souvent des artisans, des marchands, ou des membres de guildes.",
    "Militaire": "PNJ que l'on peut rencontrer dans des contextes militaires, comme les camps d'entraînement ou les forteresses. Ces personnages sont souvent des soldats, des officiers, ou des stratèges.",
    "Port/Quai": "PNJ que l'on peut rencontrer dans des lieux maritimes, comme les ports ou les quais. Ces personnages sont souvent des marins, des pêcheurs, ou des marchands.",
    "Temple/Église": "PNJ que l'on peut rencontrer dans des lieux sacrés, comme les temples ou les églises. Ces personnages sont souvent des prêtres, des moines, ou des fidèles.",
    "Rue/Place Publique": "PNJ que l'on peut rencontrer dans les rues ou les places publiques des villes et villages. Ces endroits sont animés et propices aux rencontres fortuites."
};

document.getElementById('category').addEventListener('change', function() {
    const selectedCategory = this.value;
    const description = categoryDescriptions[selectedCategory] || "";
    console.log("Category changed to:", selectedCategory);
    document.getElementById('category-description').textContent = description;
    updateFilters(); // Mettre à jour les filtres actifs
    loadData(); // Charger les données lorsque la catégorie change
});

document.getElementById('sexe').addEventListener('change', function() {
    console.log("Sexe filter changed.");
    updateFilters(); // Mettre à jour les filtres actifs
    loadData(); // Charger les données lorsque le sexe change
});

document.getElementById('race').addEventListener('change', function() {
    console.log("Race filter changed.");
    updateFilters(); // Mettre à jour les filtres actifs
    loadData(); // Charger les données lorsque la race change
});

document.getElementById('keyword').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Empêcher la soumission du formulaire
        console.log("Keyword search initiated.");
        updateFilters(); // Mettre à jour les filtres actifs
        loadData('search'); // Charger les données par mot-clé
    }
});

document.getElementById('search-icon').addEventListener('click', () => {
    console.log("Search button clicked.");
    updateFilters();
    loadData('search');
});

$(document).ready(function() {
    $('.navbar-toggler').click(function() {
        $('.navbar-nav').toggleClass('show');
    });
});

document.getElementById('random-btn').addEventListener('click', function() {
    console.log("Random PNJ button clicked.");
    loadData('random'); // Charger un PNJ aléatoire
});

document.getElementById('reset-btn').addEventListener('click', function() {
    console.log("Reset filters button clicked.");
    document.getElementById('category').value = '';
    document.getElementById('sexe').value = '';
    document.getElementById('race').value = '';
    document.getElementById('keyword').value = '';
    document.getElementById('category-description').textContent = '';
    clearFilters(); // Effacer les filtres actifs
    loadData(); // Réinitialiser les filtres
});

function updateFilters() {
    const filtersDiv = document.getElementById('active-filters');
    filtersDiv.innerHTML = ''; // Effacer tous les filtres actifs

    const category = document.getElementById('category').value;
    const sexe = document.getElementById('sexe').value;
    const race = document.getElementById('race').value;
    const keyword = document.getElementById('keyword').value;

    console.log("Updating filters with:", { category, sexe, race, keyword });

    if (category) {
        const filterTag = createFilterTag('Localisation', category);
        filtersDiv.appendChild(filterTag);
    }
    if (sexe) {
        const filterTag = createFilterTag('Sexe', sexe);
        filtersDiv.appendChild(filterTag);
    }
    if (race) {
        const filterTag = createFilterTag('Race', race);
        filtersDiv.appendChild(filterTag);
    }
    if (keyword) {
        const filterTag = createFilterTag('Mot-clé', keyword);
        filtersDiv.appendChild(filterTag);
    }
}
$(document).on('change', '.custom-file-input', function(event) {
    var inputFile = event.currentTarget;
    $(inputFile).parent()
        .find('.custom-file-label')
        .html(inputFile.files[0].name);
});

function createFilterTag(type, value) {
    const filterTag = document.createElement('span');
    filterTag.className = 'active-filter';
    filterTag.textContent = `${type}: ${value}`;
    filterTag.addEventListener('click', function() {
        removeFilter(type);
        filterTag.remove();
        console.log(`Filter removed: ${type}`);
        loadData(); // Charger les données après la suppression du filtre
    });
    return filterTag;
}

function removeFilter(type) {
    document.getElementById(type === 'Mot-clé' ? 'keyword' : type.toLowerCase()).value = '';
}

function clearFilters() {
    const filtersDiv = document.getElementById('active-filters');
    filtersDiv.innerHTML = ''; // Effacer tous les filtres actifs
}

function escapeHtml(string) {
    const entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };
    return String(string).replace(/[&<>"'`=\/]/g, s => entityMap[s]);
}

function escapeAttribute(string) {
    if (typeof string !== 'string') {
        console.error("Expected a string but got:", string);
        return '';
    }
    return string.replace(/'/g, '&#39;');
}

// Variable globale pour stocker les paramètres du PNJ
let params = {};

function loadData(action = 'filter', page = 1) {
    const category = document.getElementById('category').value;
    const sexe = document.getElementById('sexe').value;
    const race = document.getElementById('race').value;
    const keyword = document.getElementById('keyword').value;

    // Afficher le spinner de chargement
    const spinner = document.querySelector('.loading-spinner');
    spinner.style.display = 'block';

    console.log("Loading data with parameters:", { action, page, category, sexe, race, keyword });

    $.post('/get_data', {
        category: category,
        sexe: sexe,
        race: race,
        keyword: keyword,
        action: action,
        page: page
    }, function(data) {
        console.log("Data received from server:", JSON.stringify(data, null, 2));

        // Masquer le spinner de chargement
        spinner.style.display = 'none';

        const resultsDiv = $('#results');
        resultsDiv.empty();
        if (data.pnjs && data.pnjs.length > 0) {
            data.pnjs.forEach((row, index) => {
                // Utiliser la méthode habituelle pour gérer les caractères spéciaux dans le nom
                const escapedNom = escapeHtml(row.Nom);
                const finalNom = escapeAttribute(escapedNom);
                // Ici, on utilise finalNom dans l'objet params pour éviter "undefined" plus tard
                const paramsObj = {
                    id: row.Id,
                    nom: finalNom,
                    image: row.Image
                };
                // On encode l'objet params en une chaîne JSON, puis on l'encode pour être inséré dans l'attribut onclick
                const paramsStr = encodeURIComponent(JSON.stringify(paramsObj));

                // Créer un ID unique pour le bouton
                const buttonId = `imageBtn-${row.Id}`;

                const card = `
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">${finalNom}</h5>
                                <h6 class="card-subtitle mb-2 text-muted">(${escapeHtml(row.Sexe)} ${escapeHtml(row.Race)})</h6>
                                <p class="card-text"><strong>Localisation :</strong> ${escapeHtml(row.Catégorie)}</p>
                                <p class="card-text"><strong>Description :</strong> ${escapeHtml(row.Description)}<br>
                                <strong>Background :</strong> ${escapeHtml(row.Background)}</p>
                                <p class="card-text">
                                    <strong>Prompt :</strong>
                                    <button type="button" class="btn btn-toggle" data-toggle="collapse" data-target="#prompt-${index}">
                                        <i class="fas fa-plus-circle"></i>
                                    </button>
                                </p>
                                <div id="prompt-${index}" class="collapse">
                                    <p class="card-text prompt-text">${escapeHtml(row.Prompt)}</p>
                                </div>
                                <button id="${buttonId}" class="btn btn-custom-image mt-2" onclick="openImageModal('${paramsStr}')">
                                    <span>${(row.Image && row.Image !== "aucune") ? 'Voir l\'image' : 'Ajouter une image'}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                resultsDiv.append(card);
            });
        } else {
            resultsDiv.append('<p style="color: #ffcc66;">Aucun résultat trouvé.</p>');
        }

        // Mettre à jour les contrôles de pagination
        updatePagination(data.current_page, data.total_pages);
    }, 'json').fail(function(error) {
        console.error("Error loading data:", error);
    });
}

function updatePagination(currentPage, totalPages) {
    const paginationDiv = $('#pagination');
    paginationDiv.empty();

    console.log("Updating pagination:", { currentPage, totalPages });

    // Lien "Précédent"
    if (currentPage > 1) {
        paginationDiv.append(`
            <li class="page-item">
                <a class="page-link" href="#" aria-label="Previous" onclick="loadData('filter', ${currentPage - 1})">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `);
    }

    // Liens pour chaque page
    for (let i = 1; i <= totalPages; i++) {
        paginationDiv.append(`
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadData('filter', ${i})">${i}</a>
            </li>
        `);
    }

    // Lien "Suivant"
    if (currentPage < totalPages) {
        paginationDiv.append(`
            <li class="page-item">
                <a class="page-link" href="#" aria-label="Next" onclick="loadData('filter', ${currentPage + 1})">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `);
    }
}

// Fonction pour échapper les caractères spéciaux dans le HTML
function escapeHtml(string) {
    const entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;'
    };
    return String(string).replace(/[&<>"'/]/g, s => entityMap[s]);
}

// Fonction pour échapper les attributs HTML (mais ici on l'utilise pour obtenir un nom adapté)
function escapeAttribute(string) {
    return String(string).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Charger les données dès le chargement de la page
$(document).ready(function() {
    loadData();
});

function openImageModal(encodedParams) {
    // Décoder la chaîne encodée puis la parser
    const decodedParamsStr = decodeURIComponent(encodedParams);
    const p = JSON.parse(decodedParamsStr);

    params = p; // Mise à jour de la variable globale

    const modal = $('#imageModal');
    const modalImage = $('#modalImage');
    const uploadForm = $('#image-upload-form');
    const uploadSection = $('#uploadSection');
    const pnjName = $('#pnjName');
    const imageLoadingSpinner = $('#imageLoadingSpinner');

    // Afficher le spinner de chargement et masquer l'image
    imageLoadingSpinner.show();
    modalImage.hide();

    // Convertir les entités HTML en texte lisible
    const decodedNom = $('<textarea />').html(params.nom).text();
    pnjName.text(decodedNom);

    // Stocker l'ID du PNJ dans le formulaire d'upload
    uploadForm.attr('data-id', params.id);

    if (params.image && params.image !== "aucune") {
        modalImage.attr('src', `/static/images/pnj/${params.id}.jpg`);
        uploadSection.hide();
    } else {
        modalImage.attr('src', `/static/images/default-pnj.png`);
        uploadSection.show();
    }

    modalImage.off('load').on('load', function() {
        imageLoadingSpinner.hide();
        modalImage.show();
    });

    modal.modal('show');
}


function uploadImage() {
    const form = document.getElementById('image-upload-form');
    const fileInput = form.querySelector('input[name="image"]');
    const id = form.getAttribute('data-id'); // Récupérer l'ID du PNJ

    // Vérifier si une image a été sélectionnée
    if (!fileInput.files[0]) {
        alert('Veuillez sélectionner une image avant de télécharger.');
        return;
    }

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('id', id);

    console.log("Uploading image for PNJ ID:", id);

    // Afficher la barre de progression
    $('#uploadProgress').show();

    // Désactiver les boutons pendant l'upload
    const uploadButton = $(form).find('button[onclick="uploadImage()"]');
    const cancelButton = $(form).find('button[data-dismiss="modal"]');
    uploadButton.prop('disabled', true);
    cancelButton.prop('disabled', true);
    uploadButton.text('Téléchargement en cours...');

    $.ajax({
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            // Suivi de la progression de l'upload
            xhr.upload.addEventListener("progress", function(evt) {
                if (evt.lengthComputable) {
                    var percentComplete = Math.round((evt.loaded / evt.total) * 100);
                    $('#uploadProgress .progress-bar').css('width', percentComplete + '%');
                    $('#uploadProgress .progress-bar').attr('aria-valuenow', percentComplete);
                    $('#uploadProgress .progress-bar').text(percentComplete + '%');
                }
            }, false);
            return xhr;
        },
        url: '/upload_image',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                alert('Image téléchargée avec succès.');

                // Mettre à jour l'image affichée dans la modale
                const newImagePath = `/static/images/pnj/${id}.jpg`;
                $('#modalImage').attr('src', newImagePath);

                // Mettre à jour params.image pour refléter l'image ajoutée
                params.image = `${id}.jpg`;

                // Mettre à jour le bouton dans la carte du PNJ
                const buttonId = `imageBtn-${id}`;
                const imageButton = document.getElementById(buttonId);
                if (imageButton) {
                    imageButton.querySelector('span').textContent = 'Voir l\'image';

                    // Mettre à jour l'attribut onclick du bouton avec les nouvelles données encodées
                    const paramsObj = {
                        id: id,
                        nom: params.nom,
                        image: params.image
                    };
                    const paramsStr = encodeURIComponent(JSON.stringify(paramsObj));
                    imageButton.setAttribute('onclick', `openImageModal('${paramsStr}')`);
                }

                // Cacher le message "Aucune image personnalisée..."
                $('#messageNoImage').hide();

                // Cacher la section d'upload
                $('#uploadSection').hide();

                // Réinitialiser l'interface de l'upload
                resetUploadUI();
            } else {
                alert('Échec du téléchargement de l\'image.');
                resetUploadUI();
            }
        },
        error: function() {
            alert('Une erreur s\'est produite lors du téléchargement de l\'image.');
            resetUploadUI();
        }
    });

    function resetUploadUI() {
        // Réactiver les boutons et remettre le texte initial
        uploadButton.prop('disabled', false);
        cancelButton.prop('disabled', false);
        uploadButton.text('Télécharger');

        // Réinitialiser et cacher la barre de progression
        $('#uploadProgress .progress-bar').css('width', '0%');
        $('#uploadProgress .progress-bar').attr('aria-valuenow', '0');
        $('#uploadProgress .progress-bar').text('');
        $('#uploadProgress').hide();
    }
}




// Charger les données initiales lors du chargement de la page
loadData();

// Charger les races dynamiquement
$.post('/get_races', function(races) {
    const raceSelect = $('#race');
    races.forEach(race => {
        raceSelect.append(new Option(race, race));
    });
}, 'json').fail(function(error) {
    console.error("Error loading races:", error);
});

function updatePagination(currentPage, totalPages) {
    const paginationDiv = $('#pagination');
    paginationDiv.empty();

    console.log("Updating pagination:", { currentPage, totalPages });

    // Ajouter le lien "Précédent"
    if (currentPage > 1) {
        paginationDiv.append(`
            <li class="page-item">
                <a class="page-link" href="#" aria-label="Previous" onclick="loadData('filter', ${currentPage - 1})">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `);
    }

    // Ajouter les liens des pages
    for (let i = 1; i <= totalPages; i++) {
        paginationDiv.append(`
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadData('filter', ${i})">${i}</a>
            </li>
        `);
    }

    // Ajouter le lien "Suivant"
    if (currentPage < totalPages) {
        paginationDiv.append(`
            <li class="page-item">
                <a class="page-link" href="#" aria-label="Next" onclick="loadData('filter', ${currentPage + 1})">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `);
    }
}