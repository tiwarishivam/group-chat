from flask import session
from flask_socketio import emit, join_room, leave_room
from app import socketio
from flask_login import current_user


@socketio.on('joined')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    emit('status', {'username':session.get('name'),'message':'connected'}, room=room)


@socketio.on('my event')
def handle_my_custom_event(message,methods=['GET', 'POST']):
    print('received my event: ' + str(message))
    message['username']=session.get('name')
    room=session.get('room')
    print(room)
    emit('my response', message, room=room)


@socketio.on('left')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'username':session.get('name'),'message':'disconnected'}, room=room)
