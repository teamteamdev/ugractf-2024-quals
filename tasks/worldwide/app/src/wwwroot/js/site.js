function updateLanguage(lang){
    fetch(`${window.location.pathname}localization/`, {
        method: 'GET',
        headers:{
            'Accept-Language': lang
        }
    }).then(
        response => response.text()
    ).then(
        response => document.getElementById('home-page').innerHTML = response
    ).catch(
        err => console.error(err)
    )
}