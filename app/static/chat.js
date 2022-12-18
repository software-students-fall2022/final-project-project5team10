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
        const timestamp = document.createElement('span');
        const br = document.createElement('br');
        namestamp.innerHTML=data.username;
        timestamp.innerHTML=data.timestamp;
        p.innerHTML= namestamp.outerHTML + br.outerHTML + data.msg 
        + br.outerHTML+timestamp.outerHTML;
        document.querySelector('#display-chat').append(p);
    });



    document.querySelector('#send-msg').onclick = () =>{
        socket.send({'msg':document.querySelector('#user-msg').value, 
        'username':username});
    }

    // document.querySelectorAll('.select-room').forEach(p =>{
    //     p.onclick = () =>{
    //         let newRoom = p.innerHTML;
    //         if (newRoom == room){
    //             msg = `You are already in ${room} room.`;
    //             printSysMsg(msg);
    //         }
    //         else{
    //             leaveRoom(room);
    //             joinRoom(newRoom);
    //             room=newRoom;
    //         }
    //     }
    // });

    // function leaveRoom(room){
    //     socket.emit('levae', {'username': username, 'room':room});
    // }
    // function joinRoom(room){
    //     socket.emit('join', {'username': username, 'room': room});
    //     //clear msg
    //     document.querySelector('#display-chat').innerHTML='';
    // }
    // function printSysMsg(msg){
    //     const p = document.createElement('p');
    //     p.innerHTML=msg;
    //     document.querySelector('#display-chat').append(p);
    //}
}