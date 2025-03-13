function toggleSecretForm() {
    var formDiv = document.getElementById("add-secrets");
    if(formDiv){

        if(formDiv.style){
            if (formDiv.style.display === "none" || formDiv.style.display === "") {
                formDiv.style.display = "block";
            } else {
                formDiv.style.display = "none";
            }
        }
        
    }
}


function addNominees() {
    var container = document.getElementById("nominee-fields");
    var index = container.children.length;
    var newField = document.createElement("div");
    newField.setAttribute("id", "nominee-field-" + index);
    newField.innerHTML  = `
        <div>
            <label>Nominee Name:</label>
            <input type="text" name="nominees-${index}-name" required>
            <label>email:</label>
            <input type="text" name="nominees-${index}-email_id" required>
            <button type="button" onclick="removeNominee('nominee-field-${index}')">Remove</button>
        </div>
    `;
    container.appendChild(newField);
}

function removeNominee(id) {
    console.log("remove" + id);
    var field = document.getElementById(id);
    if (field) {
        field.remove();
    }
}
