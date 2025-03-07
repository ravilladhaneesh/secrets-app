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
function addNominees() {
    var container = document.getElementById("nominee-fields");
    var index = container.children.length;
    var newField = document.createElement("div");
    newField.setAttribute("id", "nominee-field-" + index);
    newField.innerHTML  = `
        <div>
            <label>Nominee Name:</label>
            <input type="text" name="nominees-${index}-name" required>
            <label>Email:</label>
            <input type="text" name="nominees-${index}-email_id" required>
            <button type="button" onclick="removeNominee('nominee-field-${index}')">Remove</button>
        </div>
    `;
    container.appendChild(newField);
}

// Remove nominee input field
function removeNominee(id) {
    var field = document.getElementById(id);
    if (field) {
        field.remove();
    }
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
}