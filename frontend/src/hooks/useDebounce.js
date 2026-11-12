import { useEffect, useState } from 'react'

// Devuelve `valor` recién cuando dejó de cambiar durante `espera` ms. Sirve
// para no disparar una búsqueda con cada tecla.
export function useDebounce(valor, espera = 400) {
  const [demorado, setDemorado] = useState(valor)

  useEffect(() => {
    const temporizador = setTimeout(() => setDemorado(valor), espera)
    return () => clearTimeout(temporizador)
  }, [valor, espera])

  return demorado
}
