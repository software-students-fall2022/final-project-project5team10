document.addEventListener('DOMContentLoaded', main());

function main(){
    const socket = io();

    //connect to socketio debug
    socket.on('connect', ()=>{
        console.log('user connected');
    });

    socket.on('message', data =>{
        const p = document.createElement('p');
        const namestamp = document.createElement('span');
        const br = document.createElement('br');
        namestamp.innerHTML=data.username;
        p.innerHTML= namestamp.outerHTML + br.outerHTML + data.msg + br.outerHTML;
        document.querySelector('#display-chat').append(p);
    });

    socket.on('some-event',data=>{
        console.log(data);
    });

    document.querySelector('#send-msg').onclick = () =>{
        socket.send({'msg':document.querySelector('#user-msg').value, 'username':username});
    }
}