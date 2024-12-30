const comeback=document.querySelector('#comeback');
const comeback2=document.querySelector('#comeback2');
const authForm1 = document.querySelector('.auth-form:first-child');
const authForm2=document.querySelector('.auth-form:last-child');
const modal =document.querySelector('.modal');
const register=document.querySelector('#register');
const register2=document.querySelector('#register2');
const login=document.querySelector('#login');
const login2=document.querySelector('#login2');
const toastContainer = document.querySelector('.toast-container');
const liveToast = document.getElementById('liveToast');

function showRegister(){
    modal.classList.add('open');
    authForm1.style.display='block';
    authForm2.style.display='none';
}

function showLogin(){
    modal.classList.add('open');
    authForm2.style.display='block';
    authForm1.style.display='none';
}

function remove(){
    modal.classList.remove('open');
    if (toastContainer) {
        toastContainer.style.display = 'none';
    }
}

register.addEventListener('click',showRegister);
register2.addEventListener('click',showRegister);
comeback.addEventListener('click',remove);
login.addEventListener('click',showLogin);
comeback2.addEventListener('click',remove);
login2.addEventListener('click',showLogin);

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('registered')) {
        if (toastContainer) {
            toastContainer.style.display = 'block';
        }
        showLogin();
    }
});