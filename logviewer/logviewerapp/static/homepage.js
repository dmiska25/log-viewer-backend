
// Side Menu
$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });
});


// details screen
function loadDetails(id) {
    // make htmx call with id
    htmx.ajax(
        'GET', 
        `${id}`, 
        {target: '#log-details', swap: 'innerHTML'}
    ).then(() => {
        // If details screen is closed, animate render show
        document.getElementById("mySidepanel").style.width = "45%";
    });
}

function closeDetails() {
    // animate render hidden
    document.getElementById("mySidepanel").style.width = "0";
}