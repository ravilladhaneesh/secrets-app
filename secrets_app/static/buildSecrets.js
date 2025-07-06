// Toggle visibility of the "Add Secret" form
function toggleSecretForm() {
    var formDiv = document.getElementById("add-secrets");
    var tableDiv = document.getElementById("secrets-table");
    
    if (formDiv.style.display === "none" || formDiv.style.display === "") {
        formDiv.style.display = "block";  // Show the form
        tableDiv.style.display = "none";  // Hide the table
    } else {
        formDiv.style.display = "none";  // Hide the form
        tableDiv.style.display = "table";  // Show the table
    }
}

// Cancel the "Add Secret" form and show the table again
function cancelSecretForm() {
    document.getElementById("add-secrets").style.display = "none";
    document.getElementById("secrets-table").style.display = "table";  // Show the secrets table
}

// Add nominee input fields dynamically
// function addNominees() {
//     var container = document.getElementById("nominee-fields");
//     // var index = container.children.length;
//     var index = findFirstMissingValue(container);
//     var newField = document.createElement("div");
//     newField.setAttribute("id", "nominee-field-" + index);
//     newField.innerHTML  = `
//         <div>
//             <label>Nominee Name:</label>
//             <input type="text" name="nominees-${index}-name" required>
//             <label>Email:</label>
//             <input type="text" name="nominees-${index}-email_id" required>
//             <button class='remove-nominee-btn' type="button" onclick="removeNominee('nominee-field-${index}')">Remove</button>
//         </div>
//     `;
//     container.appendChild(newField);
// }


function addNominees() {
    const container = document.getElementById("nominee-fields");
    const index = findFirstMissingValue(container);

    const nomineeDiv = document.createElement("div");
    nomineeDiv.setAttribute("id", `nominee-field-${index}`);
    nomineeDiv.className = "border rounded p-3 mb-3 position-relative";

    nomineeDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-2">
                <label class="form-label">Nominee Name:</label>
                <input type="text" name="nominees-${index}-name" class="mt-1 block w-64 rounded-md border border-gray-300 px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500" required>
            </div>
            <div class="col-md-6 mb-2">
                <label class="form-label">Email:</label>
                <input type="email" name="nominees-${index}-email_id" class="mt-1 block w-64 rounded-md border border-gray-300 px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500" required>
            </div>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2"
            onclick="removeNominee('nominee-field-${index}')">
            Remove
        </button>
    `;

    container.appendChild(nomineeDiv);
}


// Remove nominee input field
function removeNominee(id) {
    var container = document.getElementById("nominee-fields");
    var field = document.getElementById(id);
    if (field) {
        field.remove();
    }
    container.removeChild(id);
}

// Show secret details in a popup
function showSecretDetails(secret) {
    document.getElementById('overlay').style.display = 'block';
    
    document.getElementById('secret-name').innerText = `Secret Name: ${secret.fieldName}`;
    document.getElementById('secret-value').innerText = `Value: ${secret.fieldSecret}`;
    var nomineeList = document.getElementById('nominee-list');
    nomineeList.innerHTML = '';
    secret.nominees.forEach(function(nominee) {
        var li = document.createElement('li');
        li.innerText = `${nominee.name} - ${nominee.email_id}`;
        nomineeList.appendChild(li);
    });
    document.getElementById('overlay').style.display = 'block';
    document.getElementById('details-popup').style.display = 'block';

}


// Close the secret details popup
function closePopup() {
    document.getElementById('overlay').style.display = 'none';
    document.getElementById('details-popup').style.display = 'none';
    document.getElementById('del-secret-consent').style.display = 'none';
}

function findFirstMissingValue(divObj){
    var len = divObj.children.length;
    let indexes = [];
    for(let div in divObj.children) {
        indexes.push(divObj.children[div].id);
    }
    for (let i=0;i < len; i++){
        if(!indexes.includes('nominee-field-'+i))
            return i;
    }
    return len;
}

function showDeleteAlert(secret, deleteUrl) {
    document.getElementById('overlay').style.display = 'flex';

    document.getElementById('del-secret-name').innerText = `Secret Name: ${secret.fieldName}`;

    var delSecretConsent = document.getElementById('del-secret-consent');
    delSecretConsent.style.display = 'block';

    var delBtn = delSecretConsent.querySelector('.del-secret-btn');

    // ✅ Remove old click handlers
    var newDelBtn = delBtn.cloneNode(true);
    delBtn.parentNode.replaceChild(newDelBtn, delBtn);

    // ✅ Add a new one
    newDelBtn.addEventListener('click', () => {
        window.location.href = deleteUrl;
    });
}
