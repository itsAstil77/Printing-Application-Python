function toggleSelectAll(selectAllCheckbox) {
    document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function toggleRowSelection(row) {
    const checkbox = row.querySelector('.employee-checkbox');
    checkbox.checked = !checkbox.checked;
}

function filterEmployees() {
    let input = document.getElementById("search-box").value.toLowerCase();
    let rows = document.querySelectorAll("tbody tr");  

    rows.forEach(row => {
        let text = Array.from(row.children)  
                         .map(cell => cell.textContent.toLowerCase())  
                         .join(" ");  

        if (text.includes(input)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

function generateSelectedIdCards() {
    const checkboxes = document.querySelectorAll('.employee-checkbox:checked');
    const selectedEmployeeIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    const selectedIdCardType = document.getElementById('id-card-type-selector').value; 

    if (selectedEmployeeIds.length === 0) {
        alert('Please select at least one employee.');
        return;
    }

    document.getElementById("loading-popup").style.display = "flex";

    fetch('/generate-selected-id-cards/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}' 
        },
        body: JSON.stringify({
            employee_ids: selectedEmployeeIds,
            card_type: selectedIdCardType 
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loading-popup").style.display = "none";

        if (data.files && data.files.length > 0) {
            let previewWindow = window.open('', '', 'height=800,width=800');
            previewWindow.document.write(`
                <html>
                <head>
                    <title>Print ID Cards</title>
                    <style>
                        @page {
                            size: 8.56cm 5.4cm; 
                            margin: 0;
                            
                        }
                        body {
                            margin: 0;
                            padding: 0;
                            flex-direction: column;
                            align-items: center;
                        }
                        .id-card-container {
                            page-break-before: always;
                            width: auto;
                            height: auto;
                            justify-content: center;
                            align-items: center;
                            margin:0;
                            padding;0
                            
                        }
                        .id-card-container:last-child {
                            page-break-before: auto !important;
                            page-break-after: auto !important;
                        }

                        .id-card {
                            width: 8.56cm;
                            height: 5.40cm;
                            background-color: white;
                            justify-content: center;
                            align-items: center;
                            
                        }
                        .id-card img {
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                            
                        }
                        .id-card-container:not(:first-child) {
                            page-break-before: always;
                        }
                        @media print {
                            body { display: block; }
                            .id-card-container {
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                width: 100vw;
                                height: 100vh;
                                page-break-before: always;
                            }
                            button { display: none; }
                        }
                    </style>
                </head>
                <body>
            `);

            data.files.forEach(file => {
                const timestamp = new Date().getTime();
                const imageUrl = `/media/generated_id_cards/${file.split('/').pop()}?v=${timestamp}`;

                previewWindow.document.write(`
                    <div class="id-card-container">
                        <div class="id-card">
                            <img src="${imageUrl}">
                        </div>
                    </div>
                `);
            });

            previewWindow.document.write(`
                    <button onclick="window.print()">Print ID Cards</button>
                </body>
                </html>
            `);
            previewWindow.document.close();

            document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        } else {
            alert('No ID cards generated or files returned.'); 
        }
    })
    .catch(error => {
        console.error('Error generating ID cards:', error);
        document.getElementById("loading-popup").style.display = "none";
        alert('An error occurred during ID card generation. Check console for details.'); 
    });
}

function logout() {
    let confirmLogout = confirm("Are you sure you want to logout?");

    if (confirmLogout) {
        window.location.href = "/login/";
    }
}