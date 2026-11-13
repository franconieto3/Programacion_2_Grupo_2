// Avatar espera { nombre, apellido }: con la primera y la última palabra del
// nombre público de un organizador, "Bar Los Pinos" muestra "BP". Lo usan la
// ficha de un evento ("Publicado por") y la administración de organizadores.
export function avatarDeOrganizador(nombrePublico) {
  const palabras = nombrePublico.trim().split(/\s+/)
  return { nombre: palabras[0], apellido: palabras.length > 1 ? palabras.at(-1) : '' }
}
