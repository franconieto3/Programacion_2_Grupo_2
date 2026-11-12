"""Perfil del usuario autenticado (GET /auth/me): sus datos y los roles
que habilitan acciones en el frontend (organizador, administrador).

Vive fuera de app/auth para que auth no dependa de organizadores ni de
administradores: son esos modulos los que dependen de auth."""
