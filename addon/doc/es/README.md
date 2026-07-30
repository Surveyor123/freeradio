# FreeRadio — NVDA Add-on

FreeRadio es un complemento de radio por Internet para el lector de pantalla NVDA. Su principal objetivo es proporcionar a los usuarios un fácil acceso a miles de estaciones de radio por Internet. Toda la interfaz y todas las funciones se han diseñado teniendo en cuenta la accesibilidad total para NVDA.

## El Directorio de Radio Browser

FreeRadio utiliza la base de datos abierta de [Radio Browser](https://www.radio-browser.info/) por su catálogo de estaciones. Radio Browser es un directorio gratuito impulsado por la comunidad que alberga más de 50.000 estaciones de radio por Internet de todo el mundo. No se requiere registro ni cuenta y su API está abierta a todos. Cada estación incluye información sobre dirección, país, género, idioma y bitrate; las estaciones se clasifican según los votos de los usuarios. FreeRadio se conecta a esta API a través de servidores espejo ubicados en Alemania, Países Bajos y Austria; Si un servidor es inaccesible, pasa automáticamente al siguiente.

Para mantener el navegador receptivo y evitar acceder a la API en cada búsqueda o cambio de país, FreeRadio mantiene un caché local del catálogo de estaciones en el disco. Este caché se actualiza automáticamente en segundo plano según una programación periódica, por lo que la lista que ve normalmente ya está actualizada sin que usted tenga que realizar ninguna acción. También puedes forzar una resincronización inmediata en cualquier momento con el botón **Actualizar lista de estaciones** — consulta la sección [Navegador de Estaciones](#station-browser) más abajo.

## Añadir una estación a Radio Browser

Si una estación que está buscando no aparece en el directorio de Radio Browser, puedes enviarlo tú mismo a [https://www.radio-browser.info/add](https://www.radio-browser.info/add). No es necesario tener cuenta ni registrarse.

Llene el formulario en esta página:

- **Stream URL** *(requerido)* — la URL directa del flujo de audio, terminando en `.mp3`, `.aac`, `.ogg` o similar. Esta no es la dirección del sitio web de la estación; esta es la dirección del flujo  bruto de transmisión que pegarías en un reproductor multimedia. La mayoría de las estaciones publican la URL de su flujo de transmisión en su sitio web o en su sección "Escuchar en directo".
- **Station name** *(requerido)* — el nombre de la estación como debería aparecer en el directorio.
- **Homepage** — la dirección del sitio web de la estación.
- **Country and language** — seleccione el país y el idioma de transmisión en las listas desplegables.
- **Tags** — palabras clave separadas por comas, por genre o topic, por ejemplo `news`, `jazz`, `classical`. Estos se utilizan para buscar y filtrar.
- **Logo URL** — un enlace directo a la imagen del logotipo de la estación, si está disponible.

Después del envío, la estación se revisa y se añade al directorio público. Una vez aceptado, aparecerá automáticamente en los listados de países y de búsqueda de FreeRadio, ya que el directorio se actualiza desde la API en directo.

## Requisitos

- NVDA 2024.1 o posterior
- Windows 10 o posterior
- Conexión a Internet

## Instalación

Descarga el archivo `.nvda-addon`, pulsa Intro y reinicia NVDA cuando se te solicite.

## Atajos de teclado

Todos los atajos se pueden reasignar desde el Menú NVDA → Preferencias → Gestos de Entrada → FreeRadio. Estos atajos funcionan desde cualquier lugar, independientemente de qué ventana tenga el foco.

| Atajo | Función | Descripción |
|---|---|---|
| `Ctrl+Win+R` | Abrir el navegador de estaciones | Abre la ventana del navegador si está cerrada o la trae al segundo plano si ya está abierta. |
| `Ctrl+Win+P` | Pausar / reanudar | Pausa la estación actual si se está reproduciendo; se reanuda cuando está en pausa. Si no se reproduce nada, inicia la última estación o abre la lista de favoritos según su configuración. Al pulsar dos veces en sucesión rápida, irás directamente a la pestaña que elijas. Pulsar tres veces puede activar una acción separada dependiendo de su configuración. |
| `Ctrl+Win+S` | Detener | Detiene completamente la estación actual y reinicia el reproductor. |
| `Ctrl+Win+→` | Siguiente favorito | Salta  a la siguiente estación en la lista de favoritos. Vuelve al principio y al final de la lista. |
| `Ctrl+Win+←` | Favorito anterior | Salta a la estación anterior en la lista de favoritos. Salta al final cuando está al principio. |
| `Ctrl+Win+↑` | Aumentar el volumen | Aumenta el volumen de 5 ; máximo 100. |
| `Ctrl+Win+↓` | Disminuir el volumen | Disminuye el volumen de 5 ; mínimo 0. |
| `Ctrl+Win+V` | Añadir a favoritos | Añade la estación que se está reproduciendo actualmente a la lista de favoritos. Anuncia si la emisora ya está en la lista. |
| `Ctrl+Win+I` | Información de la Estación | Anuncia el nombre de la estación que se está reproduciendo actualmente. Pulsa dos veces para mostrar los detalles como el país, el género y el bitrate en un diálogo. Pulsa tres veces para copiar la información de la pista actual (metadatos ICY) al portapapeles si está disponible; Si no hay metadatos presentes, inicia el reconocimiento de música de Shazam en su lugar. Pulsa cuatro veces para forzar el reconocimiento de música en caso de metadatos ICY incorrectos. |
| `Ctrl+Win+M` | Espejo de audio | Poner en espejo el flujo actual hacia un dispositivo de salida de audio adicional simultáneamente. Pulsa nuevamente para detener la puesta en espejo. |
| `Ctrl+Win+E` | Grabación instantánea | Pulsa una vez para comenzar a grabar la estación actual; pulsa nuevamente para detener. Pulsa **dos veces** para comenzar una **grabación de la canción**: El archivo lleva el nombre de la pista actual y la grabación se detiene automáticamente cuando cambia la pista. Pulsa nuevamente dos veces mientras la grabación de una canción está activa para detenerla antes de tiempo. La reproducción continúa sin interrupción en todos los modos de grabación. Solo disponible para estaciones que transmiten metadatos ICY. |
| `Ctrl+Win+W` | Abrir la carpeta de grabaciones | Abre la carpeta que contiene los archivos guardados en el Explorador de archivos. |
| `Ctrl+Win+J` | Retroceso del desplazamiento temporal | Retrocede la radio en directo 15 segundos. La primera pulsación entra en el modo de desplazamiento temporal; cada pulsación adicional retrocede 15 segundos más, hasta el límite del búfer (~10 minutos). Requiere que el búfer de desplazamiento temporal esté habilitado en Ajustes. |
| `Ctrl+Win+K` | Avance rápido del desplazamiento temporal | Avanza 15 segundos mientras se está en modo de desplazamiento temporal. Una vez alcanzado el borde del directo, la reproducción vuelve automáticamente al directo y este comando no tiene efecto hasta que se retroceda de nuevo. |
| `Ctrl+Win+T` | Alternar búfer de desplazamiento temporal | Habilita o deshabilita el búfer de desplazamiento temporal al instante, reflejando la casilla de Ajustes. Al deshabilitarlo, vuelve inmediatamente al directo si estaba en modo de desplazamiento temporal y detiene la captura en segundo plano. |
| *((no asignado)* | Alternar notificaciones silenciosas | Alternar la configuración de Silenciar notificaciones sobre la marcha. Asignar una combinación de teclas a través del Menú NVDA → Preferencias → Gestos de Entrada → FreeRadio. |
| *(no asignado)* | Reproducir estación favorita directamente | Cada estación de la lista de favoritos aparece como una entrada individual en el Menú NVDA → Preferencias → Gestos de Entrada → **Estaciones FreeRadio**. Asigna un atajo de teclado a cualquier estación para iniciarla al instante desde cualquier lugar, sin abrir el navegador. |

Los atajos siguientes/anteriores sólo recorren la lista de favoritos; No funcionan con la lista de todas las estaciones. Cuando una lista tiene el foco en la ventana del navegador, las teclas de flecha izquierda y derecha tienen el mismo propósito — ver la sección de Atajos en el cuadro de diálogo.

## Navegador de Estaciones

FreeRadio también añade un subMenú **FreeRadio** en el Menú Herramientas de NVDA. Desde allí puede abrir directamente el Navegador de Estaciones y los Ajustes de FreeRadio.

La ventana abierta con `Ctrl+Win+R` contiene cinco pestañas: Todas las estaciones, Favoritos, Grabación, Temporizador y Canciones favoritas. Puedes navegar entre las pestañas con `Ctrl+Tab`.

Cuando se abre la pestaña Todas las estaciones, las 1000 estaciones más votadas se cargan automáticamente desde Radio Browser. Al seleccionar un país de la lista desplegable, se actualiza la lista para mostrar estaciones de ese país. Al escribir en el cuadro de búsqueda se realiza instantáneamente una búsqueda completa en toda la base de datos de Radio Browser simultáneamente por nombre, país y género.

La lista desplegable **Dispositivo de salida** en la parte inferior de la ventana del navegador (fuera de las pestañas) enumera todos los dispositivos de salida de audio reconocidos por BASS. Al seleccionar un dispositivo, se redirige inmediatamente la salida de audio a él y se guarda la elección de forma permanente; el mismo dispositivo se utiliza automáticamente en la siguiente sesión. Si el dispositivo seleccionado no está conectado, el complemento vuelve automáticamente al valor predeterminado del sistema. Este control solo funciona cuando el BASS backend está activo.

Los controles de **Volumen** (0–200) y **Efectos** en la misma área se puede ajustar en cualquier momento cuando la ventana está abierta. Desde la lista de Efectos, Coro, Compresión, Distorsión, Eco, Flanger, Gargle, Reverberación, EQ: Bass Boost, EQ: Treble Boost y EQ: Vocal Boost se puede activar simultáneamente; Los cambios se aplican instantáneamente al flujo activo. Cada efecto también se puede alternar instantáneamente con `Ctrl+1` hasta `Ctrl+0` sin salir del teclado — consulta la sección [Atajos del Efecto](#effect-shortcuts). Estos controles solo son completamente funcionales cuando el BASS backend está activo.

Cuando uno o más efectos de EQ están habilitados, aparece un **control de ganancia** para cada banda activa. La ganancia se puede configurar entre −15 dB y +15 dB; los valores predeterminados son Bass +9 dB, Treble +9 dB, y Vocal +6 dB. Los controles de ganancia se muestran solo para las bandas de EQ que están marcadas actualmente y se ocultan automáticamente cuando un efecto de EQ no está marcado. Los valores de ganancia se guardan globalmente y se restauran en la siguiente sesión.

El botón **Reproducir/Pausar** También se encuentra en la parte inferior de la ventana. Si no se reproduce ninguna estación, se inicia la estación seleccionada; si ya se está reproduciendo una emisora, la reproducción se interrumpe.

El botón **Actualizar lista de estaciones** vuelve a sincronizar el catálogo de estaciones locales desde la API Radio Browser inmediatamente, en lugar de esperar la actualización periódica en segundo plano. Mientras se ejecuta la actualización, el botón está desactivado y NVDA anuncia que hay una actualización en curso; Si lo pulsas nuevamente antes de que finalice la actualización actual, NVDA te informará que ya hay una en marcha. Una vez que se completa la actualización, NVDA anuncia que la lista de estaciones se ha actualizado y los resultados de búsqueda o la lista de países mostrados actualmente se actualizan automáticamente para reflejar los nuevos datos.

Cuando se selecciona una estación en la lista, el botón **Detalles de la estación** muestra información como el país, el idioma, el género, el formato, el bitrate, el sitio web y el flujo URL en un cuadro de diálogo separado. Cada campo aparece en su propio cuadro de texto de solo lectura; puedes moverte entre los campos con Tab y copia toda la información al portapapeles de una vez con el botón **Copiar todo al portapapeles**. Este botón está disponible en las pestañas Todas las estaciones y Favoritos.

### Menú Contextual de la Estación

Haga clic derecho en una estación en la lista Todas las estaciones o Favoritos, o selecciónela y pulse la tecla Aplicaciones o `Shift+F10`, para abrir un menú contextual con acciones rápidas:

- **Detalles de la estación** — igual que el botón Detalles de la estación descrito anteriormente.
- **Añadir a favoritos** *(pestaña Todas las estaciones)* / **Eliminar estación** *(pestaña Favoritos)*.
- **Renombrar la estación** *(pestaña Favoritos)* — igual que `F9`.
- **Guardar perfil de audio para esta estación** / **Borrar perfil de audio** *(pestaña Favoritos)* — consulta la sección [Perfil de Audio de la Estación](#station-audio-profile).
- **Probar URL** — comprueba si se puede acceder actualmente al flujo de la estación seleccionada sin iniciar la reproducción y anuncia el resultado (accesible o el motivo del error, como un error HTTP o tiempo de espera de red).

Sólo los elementos relevantes para la pestaña y selección actual se muestran como disponibles.

### Atajos en el cuadro de diálogo

Las siguientes teclas solo funcionan cuando la ventana del Navegador de Estaciones está activa.

### Teclas F

| Atajo | Función | Descripción |
|---|---|---|
| `F1` | Guía de ayuda | Abre el archivo de ayuda del complemento en el navegador predeterminado. Primero se busca la guía del idiomas NVDA activo; si no se encuentra, se abre la guía predeterminada. |
| `F2` | que esta reproduciendo  | Anuncia la estación que se está reproduciendo actualmente y el nombre de la pista. Pulsa dos veces para mostrar los detalles como el país, el género y el bitrate en un diálogo. Pulsa tres veces para copiar la información de la pista actual (metadatos ICY) al portapapeles si está disponible; si no hay metadatos presentes, inicia el reconocimiento de música de Shazam en su lugar. Pulsa cuatro veces para forzar el reconocimiento de música en caso de metadatos ICY incorrectos. |
| `F3` | Estación anterior | Salta a la estación anterior en la pestaña Todas las estaciones o Favoritos y comienza a reproducir inmediatamente. Salta al final cuando está al principio de la lista. |
| `F4` | Station suivante | Salta a la siguiente estación en la pestaña Todas las estaciones o Favoritos y comienza a reproducir inmediatamente. Vuelve al principio al final de la lista. |
| `F5` | Disminuir el volumen | Disminuye el volumen de 5 (mínimo 0). |
| `F6` | Aumentar el volumen | Aumenta el volumen de 5 (máximo 200). |
| `F7` | Pausar/reanudar | Pausa la estación actual si se está reproduciendo; se reanuda cuando está en pausa y el medio está cargado. |
| `F8` | Detener | Detiene completamente la estación actual y reinicia el reproductor. |
| `F9` | Renombrar | Abre el cuadro de diálogo para renombrar la estación enfocada en la pestaña Favoritos. |

### Lista y Atajos de Navegación

| Atajo | Función | Descripción |
|---|---|---|
| `→` | Siguiente estación | Cuando la lista Todas las estaciones o Favoritos esté enfocada, salta a la siguiente estación y la reproduce inmediatamente. Vuelve al principio al final de la lista. |
| `←` | Estación anterior | Cuando la lista Todas las estaciones o Favoritos está enfocada, salta a la estación anterior y la reproduce inmediatamente. Salta al final cuando está al principio. |
| `Intro` | Reproducir | Cuando la lista Todas las estaciones o Favoritos está enfocada, inmediatamente comienza a reproducir la estación seleccionada. Cambia a la estación seleccionada incluso si ya se está reproduciendo otra estación. |
| `Espacio` | Reproducir/Pausar | Se detiene si se está reproduciendo una estación; de lo contrario, comienza a reproducir la estación seleccionada. |
| `Ctrl+Tab` | Pestaña siguiente | Pasa a la siguiente pestaña (Todas las estaciones → Favoritos → Grabación → Temporizador → Canciones favoritas). |
| `Ctrl+Shift+Tab` | Pestaña anterior | Pasa a la pestaña anterior. |
| `Escape` | Ocultar | Oculta la ventana; el complemento continúa reproduciéndose en segundo plano. |

### Atajos de Volumen

| Atajo | Función | Descripción |
|---|---|---|
| `Ctrl+↑` | Aumentar el volumen | Aumenta el volumen de 5. Funciona sólo cuando la ventana del navegador está abierta. |
| `Ctrl+↓` | Disminuir el volumen | Disminuye el volumen de 5. Funciona sólo cuando la ventana del navegador está abierta. |

### Atajos del Efecto

| Atajo | Función | Descripción |
|---|---|---|
| `Ctrl+1` | Alternar Coro | Activa o desactiva el efecto Coro y lo aplica al flujo activo al instante. |
| `Ctrl+2` | Alternar Compresión | Activa o desactiva el efecto Compresión y lo aplica al flujo activo al instante. |
| `Ctrl+3` | Alternar Distorsión | Activa o desactiva el efecto Distorsión y lo aplica al flujo activo al instante. |
| `Ctrl+4` | Alternar Eco | Activa o desactiva el efecto Eco y lo aplica al flujo activo al instante. |
| `Ctrl+5` | Alternar Flanger | Activa o desactiva el efecto Flanger y lo aplica al flujo activo al instante. |
| `Ctrl+6` | Alternar Gargle | Activa o desactiva el efecto Gargle y lo aplica al flujo activo al instante. |
| `Ctrl+7` | Alternar Reverberación | Activa o desactiva el efecto Reverberación y lo aplica al flujo activo al instante. |
| `Ctrl+8` | Alternar EQ: Bass Boost | Activa o desactiva la banda EQ Bass Boost y lo aplica al flujo activo al instante. |
| `Ctrl+9` | Alternar EQ: Treble Boost | Activa o desactiva la banda EQ Treble Boost y lo aplica al flujo activo al instante. |
| `Ctrl+0` | Alternar EQ: Vocal Boost | Activa o desactiva la banda EQ Vocal Boost y lo aplica al flujo activo al instante. |

Cada atajo refleja marcado o desmarcado en la entrada correspondiente en la lista **Efectos**: NVDA anuncia si el efecto fue habilitado o deshabilitado, el cambio se guarda automáticamente y el control de ganancia del EQ para esa banda (si corresponde) aparece o desaparece en consecuencia. Solo disponible cuando el BASS backend está activo.

### Atajos de la Tecla Alt

| Atajo | Función | Descripción |
|---|---|---|
| `Alt+R` | Ir al cuadro de búsqueda | Mueve el foco al cuadro de texto de búsqueda. Busca en Radio Browser con el texto en el campo de búsqueda; el nombre, el país y el género se buscan simultáneamente. |
| `Alt+V` | Añadir/Eliminar un favorito | Añade la estación seleccionada a los favoritos; lo elimina si ya está en la lista. |
| `Alt+1` | Todas las estaciones | Cambia a la pestaña Todas las estaciones. |
| `Alt+2` | Favoritos | Cambia a la pestaña Favoritos. |
| `Alt+3` | Grabación | Cambia a la pestaña Grabación. |
| `Alt+4` | Temporizador | Cambia a la pestaña Temporizador. |
| `Alt+5` | Canciones favoritas | Cambia a la pestaña Canciones favoritas. |
| `Alt+K` | Cerrar | Cierra la ventana; el complemento continúa reproduciéndose en segundo plano. |

## Favoritos

La lista de favoritos es una colección de emisoras personales almacenada permanentemente. Para añadir una estación, selecciónela de la lista y pulse el botón Añadir a favoritos o usa el atajo `Alt+V`. El mismo atajo elimina una estación que ya está en la lista cuando se selecciona.

Los favoritos se pueden jugar con `Ctrl+Win+→` y `Ctrl+Win+←`; estos atajos funcionan incluso cuando la ventana del navegador no está abierta.

Para eliminar una emisora ​​de la lista de favoritos, selecciónela y pulse el botón **Eliminar estación** o la tecla `Suprimir`. Después de la eliminación, el foco y la selección pasan automáticamente a la siguiente estación de la lista. Si la estación eliminada fue la última, el foco se mueve a la estación anterior. Si la lista queda vacía, el foco se mueve al botón Reproducir.

### Exportar e Importar Favoritos

La pestaña Favoritos incluye dos botones para hacer copias de seguridad y restaurar tu lista de estaciones:

**Exportar favoritos…** — guarda toda tu lista de favoritos en un archivo. Un cuadro de diálogo te permite elegir entre dos formatos:
- **JSON** (`.json`) — una copia de seguridad completa que conserva los nombres de las estaciones, las URLs del Stream de transmisión y todos los metadatos. Recomendado para restaurar tu lista más adelante o moverla a otro equipo.
- **Lista de reproducción M3U** (`.m3u`) — un formato de lista de reproducción estándar compatible con la mayoría de reproductores multimedia y aplicaciones de radio. Ten en cuenta que M3U no almacena todos los metadatos de la estación, por lo que restaurar desde M3U puede resultar en menos detalles que una copia de seguridad JSON.

**Importar favoritos…** — carga estaciones desde un archivo JSON o M3U exportado previamente. Después de seleccionar el archivo, se te pregunta cómo agregar las estaciones:
- **Sí (Fusionar)** — añade las estaciones importadas a tu lista existente sin eliminar ningún favorito actual. Las estaciones duplicadas no se añaden dos veces.
- **No (Reemplazar)** — borra completamente tu lista de favoritos actual y la reemplaza con el contenido del archivo importado.
- **Cancelar** — regresa al navegador sin realizar ningún cambio.

Tras una importación exitosa, la lista de favoritos, la lista de estaciones de grabación programada y la lista de estaciones del temporizador se actualizan automáticamente.

### Reordenar Favoritos

Con una estación seleccionada en la pestaña Favoritos, pulse la `coma` para entrar en modo de desplazamiento; escuchará un pitido. Navegue hasta la posición de destino con las teclas de flecha, luego pulse la `coma` nuevamente. La estación se coloca en la posición elegida y la nueva organización queda inmediatamente registrada. Al pulsar la `coma` nuevamente en la misma posición se cancela el desplazamiento.

### Atajos de Teclado Directos para Estaciones Favoritas

Cada estación de la lista de favoritos está registrada como un script independiente en el cuadro de diálogo Gestos de Entrada de NVDA, dentro de la categoría **Estaciones FreeRadio**. Puedes asignar cualquier atajo de teclado a cualquier estación y pulsarlo desde cualquier lugar — sin necesidad de abrir la ventana del navegador.

Para asignar un atajo:

1. Abre el Menú NVDA → Preferencias → Gestos de Entrada.
2. Expande la categoría **Estaciones FreeRadio**.
3. Busca la estación por nombre, selecciónala y pulsa **Añadir**.
4. Pulsa la combinación de teclas deseada y confirma.

El atajo inicia la estación de inmediato. Si la estación se elimina de favoritos, su entrada desaparece de la categoría y cualquier atajo asignado se borra automáticamente por NVDA. Cuando se añade una nueva estación a favoritos, aparece en la categoría al instante — no es necesario volver a abrir el cuadro de diálogo Gestos de Entrada.

### Añadir una Estación Personalizada

Para añadir una estación que no está en Radio Browser, use el botón Añadir una estación personalizada. En el cuadro de diálogo que aparece, ingresa el nombre de la estación y la URL del flujo  de transmisión para añadirla directamente a tus favoritos. Las estaciones personalizadas se pueden escuchar y reorganizar como cualquier otro favorito.

Dos botones adicionales están disponibles en este cuadro de diálogo:

- **Probar URL** — comprueba la URL del flujo que ingresó antes de añadir la estación y anuncia si es accesible. Útil para detectar un error tipográfico o un enlace muerto antes de que termine en su lista de favoritos.
- **Añadir al directorio de Radio Browser…** — abre la [página de envío de Radio Browser](https://www.radio-browser.info/add) en su navegador predeterminado, para que pueda compartir la estación con la comunidad más amplia de Radio Browser una vez que haya confirmado que funciona. Consulta la sección [Añadir una estación a Radio Browser](#adding-a-station-to-radio-browser) más arriba para saber qué espera el formulario de envío.

### Perfil de Audio de la Estación

La pestaña Favoritos incluye dos botones para administrar los ajustes de audio por estación:

**Guardar perfil de audio para esta estación** — guarda el nivel de volumen actual y los efectos activos (coro, EQ, etc.), y valores de ganancia de EQ como un perfil vinculado a esa estación específica. Cada vez que esa estación comienza a reproducirse, sus ajustes de volumen, efectos y ganancia guardadas se aplican automáticamente, anulando los valores predeterminados globales.

**Borrar perfil de audio** — elimina el perfil de audio guardado de la estación seleccionada. Después de borrar, la estación vuelve a los ajustes globales de volumen,  efectos y ganancia de EQ. Este botón solo está activo cuando la estación seleccionada ya tiene un perfil guardado.

Los dos botones están ubicados debajo de la lista de favoritos y solo se activan cuando se selecciona una estación de la lista.

## Reconocimiento de Música

Pulse tres veces `Ctrl+Win+I` activa el reconocimiento de música basado en Shazam para el flujo que se está reproduciendo actualmente. El reconocimiento sólo comienza cuando no hay metadatos ICY (información de la pista transmitida por la estación) disponibles; si hay metadatos presentes, se copian al portapapeles en su lugar.

El reconocimiento funciona de la siguiente manera: se captura una breve muestra de audio a partir del flujo usando ffmpeg, se aplica el algoritmo de huellas digital de Shazam y el resultado se envía a los servidores de Shazam. Si el reconocimiento tiene éxito, el título de la canción, el artista, el álbum y el año de lanzamiento serán anunciados por NVDA y copiado automáticamente al portapapeles. Si la opción **Guardar las canciones favoritas en un archivo de texto** esta activado, el resultado del reconocimiento también se añade a `likedSongs.txt`.

**Retorno de audio:** Suenan dos pitidos ascendentes cuando comienza el reconocimiento y dos pitidos descendentes cuando finaliza. Suena un pitido corto cada 2 segundos mientras el proceso está en progreso.

**Requisito:** ffmpeg.exe requerido. Un ffmpeg.exe colocado en la carpeta del complementos se utiliza automáticamente; si está en una ubicación diferente, la ruta se puede establecer en las Opciones. Descargar ffmpeg desde [ffmpeg.org](https://ffmpeg.org/download.html).

**Una nota sobre las estaciones que insertan anuncios publicitarios:** algunas estaciones muestran un anuncio publicitario breve en cada nueva conexión realizada a su flujo, aparte de la transmisión que ya estás escuchando. El reconocimiento evita muestrear ese anuncio publicitario al reutilizar la conexión del flujo en segundo plano existente de FreeRadio (la misma que se usa para el [Desplazamiento temporal (rebobinar radio en directo)](#time-shift-rewind-live-radio)) en lugar de abrir una nueva, por lo que identifica lo que realmente se está reproduciendo en lugar de un anuncio publicitario. Esto funciona automáticamente y no necesita configuración.

## Espejo de Audio

El atajo `Ctrl+Win+M` pone los espejos del flujo que se está reproduciendo actualmente en un segundo dispositivo de salida de audio simultáneamente. Esto es útil para escuchar en dos dispositivos diferentes al mismo tiempo, como altavoces y auriculares.

Al pulsar por primera vez, aparece un cuadro de diálogo de selección que enumera los dispositivos de salida disponibles. Una vez elegido el dispositivo, comienza la puesta en espejo y la reproducción principal continúa sin interrupción. Al pulsar el atajo nuevamente se detiene la la puesta en espejo.

**Casos de uso:**
- **Altavoces + auriculares** — Dejar que un invitado siga el mismo programa con los auriculares mientras tu escuchas a través de los altavoces de la computadora.
- **Configuración de grabación** — Dirija la salida principal a los altavoces  y la segunda salida a una grabadora externa o interfaz de audio para captura externa.
- **Multihabitación** — Reproduzca simultáneamente a través de un altavoz Bluetooth y el altavoz incorporado; no se necesita software adicional para transportar el audio a otra habitación.
- **Monitoreo remoto** — En una sesión de pantalla compartida o de escritorio remoto, tanto el lado local como el remoto pueden escuchar el mismo flujo simultáneamente.

> **Nota:** La puesta en espejo de audio solo está disponible cuando el BASS backend está activo. Si se cambia el volumen mientras la puesta en espejo está activo, ambas salidas se actualizan simultáneamente.

## Grabación

Las grabaciones se guardan de forma predeterminada en `Documentos\FreeRadio Recordings\`. El nombre del archivo incluye el nombre de la estación (o el título de la canción, en modo de grabación de canciones) y la hora de inicio de la grabación. La carpeta de grabaciones se puede cambiar en cualquier momento desde el Menú NVDA → Preferencias → Opciones → FreeRadio → **Carpeta de grabaciones**. Debido a que el motor de grabación se conecta directamente al flujo de transmisión, el audio se escribe en el disco tal como se recibe; no se aplica ningún procesamiento ni recodificación; La calidad de grabación es la misma que la calidad de transmisión.

**Grabación instantánea:** Mientras se reproduce una estación, pulse una vez `Ctrl+Win+E`. Pulse nuevamente para detener. La reproducción continúa sin interrupción.

**Grabación de la canción:** Pulse `Ctrl+Win+E` **dos veces** en sucesión rápida mientras se reproduce una estación que transmite metadatos ICY. La grabación comienza inmediatamente y lleva el nombre del título de la pista actual. Cuando cambia la pista, la grabación se detiene automáticamente y NVDA anuncia el nombre del archivo grabado. Si desea terminar la grabación antes del final de la pista, ppulse `Ctrl+Win+E` dos veces nuevamente. Si la estación actual no transmite metadatos ICY, la grabación de la canción no está disponible y NVDA te lo notificará.

**Grabación programada:** Abra la pestaña Grabación en el navegador. Seleccione una estación de sus favoritos, ingrese la hora de inicio en formato HH:MM y la duración en minutos, seleccione uno o más días activos y, luego elige el modo de recurrencia y el modo de grabación:

**Días activos:** Marque uno o más días de la semana. En el modo de Solo grabación, se crea una entrada separada para cada día seleccionado, colocada en la próxima ocurrencia de ese día. En el modo de Recurrencia, la grabación se repite únicamente en los días marcados. Si no se selecciona ningún día, la grabación no se restringe a días concretos.

**Modo de recurrencia:**
- **Grabar una vez** — crea una grabación única para cada día seleccionado. Cada entrada se coloca en la próxima ocurrencia de ese día; si la hora de hoy ya pasó, la entrada se traslada automáticamente a la semana siguiente.
- **Repetir semanalmente** — se repite cada semana en los días activos seleccionados hasta que se elimine de la lista de programación.

**Modo de grabación:**
- **Grabar mientras escuchas** — reproduce y graba simultáneamente. Se inicia un backend de reproducción usando el orden de prioridad BASS → VLC → PotPlayer → Windows Media Player.
- **Solo grabación** — Graba silenciosamente en segundo plano sin ninguna salida de audio; El motor de grabación se conecta directamente al flujo de  transmisión.

NVDA anuncia cuándo comienza y cuándo termina una grabación. Si NVDA se reinicia mientras hay una grabación programada activa, la grabación se reanuda automáticamente al iniciar.

Al igual que el reconocimiento de música, la grabación instantánea y de canciones reutiliza la conexión del flujo en segundo plano existente de FreeRadio cuando está disponible, en lugar de abrir una nueva, por lo que una grabación captura lo que realmente se transmite incluso en estaciones que de otro modo mostrarían un anuncio publicitario nuevo en una conexión nueva. Esto no se aplica a las grabaciones programadas **Solo grabación**, ya que ninguna estación se está reproduciendo  al momento donde ellas empiezan.

## Desplazamiento temporal (rebobinar radio en directo)

El desplazamiento temporal permite rebobinar la emisora que estás escuchando, como un DVR o una cinta de casete: pausa el momento, retrocede unos minutos y vuelve al directo cuando quieras. La reproducción no tiene que detenerse: rebobinar y avanzar ocurren al instante en el mismo flujo de audio.

Esta función está **deshabilitada por defecto**. Actívala desde el Menú NVDA → Preferencias → Opciones → FreeRadio → **Activar búfer de desplazamiento temporal (rebobinar radio en directo, ~10 minutos)**, o actívala al instante en cualquier momento con `Ctrl+Win+T`.

> **Nota:** FreeRadio ahora conserva en todo momento una pequeña captura en segundo plano de la estación que se está reproduciendo — no solo cuando esta configuración está habilitada — porque el [Reconocimiento de Música](#music-recognition) y la [Grabación](#recording) dependen de ella para el comportamiento de evasión del anuncio publicitario descrita en estas secciones. Cuando esta configuración está **deshabilitada**, esta captura en segundo plano se conserva durante aproximadamente 45 segundos y `Ctrl+Win+J`/`Ctrl+Win+K` permanecen no disponibles — solo cambia el tamaño del búfer, no si se ejecuta. Al habilitar la configuración aumenta la misma captura hasta el rebobinado completo del búfer de ~10 minutos que se describe a continuación.

### Cómo funciona

Una vez habilitado, FreeRadio captura continuamente la emisora en reproducción a un búfer local rotativo en segundo plano. El búfer almacena aproximadamente los **últimos 10 minutos** de audio; el audio más antiguo se descarta automáticamente por el frente a medida que llega audio nuevo, de modo que el búfer siempre representa el "pasado reciente" relativo al borde del directo.

- **`Ctrl+Win+J`** — Retroceder 15 segundos. La primera pulsación te lleva de la reproducción en directo a la reproducción con desplazamiento temporal, comenzando 15 segundos detrás del borde del directo. Cada pulsación adicional retrocede 15 segundos más.
- **`Ctrl+Win+K`** — Avanzar 15 segundos en modo desplazamiento temporal. Al alcanzar el borde del directo, la reproducción vuelve automáticamente al stream en directo y NVDA anuncia «Volver al directo».
- **`Ctrl+Win+T`** — Activa o desactiva toda la función. Desactivarla mientras se está en modo de desplazamiento temporal vuelve inmediatamente al directo y detiene la captura en segundo plano de la emisora actual.

La captura en segundo plano sigue funcionando todo el tiempo que se está en modo de desplazamiento temporal, de modo que el borde del directo sigue avanzando incluso mientras escuchas algo de hace unos minutos, exactamente como un DVR real.

### Habilitación y calentamiento del búfer

El búfer empieza a llenarse tan pronto como una emisora comienza a reproducirse (una vez habilitada la función), o en el momento en que habilitas la función mientras ya escuchas una emisora. Por ello, el retroceso solo es posible una vez que se hayan capturado realmente unos segundos de audio. Si pulsas `Ctrl+Win+J` inmediatamente después de cambiar de emisora, NVDA te avisará de que todavía no hay suficiente audio en el búfer. Espera unos segundos e inténtalo de nuevo.

Cambiar a una emisora diferente siempre reinicia el búfer para la nueva emisora; el audio almacenado de la emisora anterior se descarta.

### Flujos compatibles

El desplazamiento temporal funciona con la misma gama de flujos que FreeRadio ya admite:

- Flujos HTTP/HTTPS simples (MP3, AAC, OGG, etc.), incluidos servidores de tipo Shoutcast/Icecast.
- **Flujos HLS (`.m3u8`)** — FreeRadio resuelve la lista de reproducción maestra de la emisora, sigue la lista de reproducción de medios y descarga segmentos en segundo plano para mantener el búfer lleno.

En el raro caso de que la lista de reproducción de una emisora no pueda leerse en absoluto (por ejemplo, un manifiesto `.m3u8` roto o inalcanzable), NVDA te indicará que el retroceso no está disponible para esa emisora concreta.

### Requisitos y limitaciones

- **Requiere el BASS backend.** El desplazamiento temporal no está disponible cuando el BASS está deshabilitado y la reproducción vuelve a VLC, PotPlayer, o Windows Media Player. La captura en segundo plano en sí (y la función de evitar el anuncio publicitario que proporciona al Reconocimiento de Música y el de Grabación) tampoco está disponible en ese caso, ya que depende de la misma conexión basada en BASS.
- El búfer tiene aproximadamente 10 minutos; no se puede retroceder más allá de ese límite.
- El búfer es por emisora: cambiar de emisora, detener la reproducción o reiniciar NVDA lo borra y empieza de nuevo.
- La reproducción con desplazamiento temporal usa su propio archivo de búfer local y no produce una grabación guardada. Si quieres conservar el audio de forma permanente, usa también la Grabación instantánea (`Ctrl+Win+E`).

## Temporizador

Abra la pestaña Temporizador en el navegador de estaciones (`Alt+4`). Se pueden añadir dos tipos de temporizador:

**Alarma — iniciar la radio:** Comienza a reproducir automáticamente una estación seleccionada de sus favoritos a la hora especificada. Elija una estación e ingrese la hora en formato HH:MM.

**Apagado — detener la radio:** Detiene la reproducción a la hora especificada. Cuando suena el temporizador, el volumen se reduce gradualmente durante 60 segundos antes de que se detenga la reproducción. No es necesaria ninguna selección de estación; simplemente ingrese la hora.

Para ambos tipos, si la hora ingresada ya pasó, la acción se programa para el día siguiente. Si ya existe un temporizador a la misma hora (independientemente del tipo), no se permite añadir uno nuevo; se informa al usuario del conflicto y se le pide que elimine primero la entrada existente. Los temporizadores pendientes se enumeran en la pestaña; seleccione uno y pulse el botón Eliminar el temporizador seleccionado para cancelarlo.

## Opciones

Las siguientes opciones se pueden configurar desde el Menú NVDA → Preferencias → Opciones → FreeRadio:

| Opción | Descripción |
|---|---|
| Dispositivo de salida de audio (BASS backend) | Establece el dispositivo de salida de audio para la reproducción de la radio. La lista incluye todos los dispositivos del sistema BASS-compatible más una opción "valor predeterminado del sistema". Los cambios se aplican inmediatamente después de guardarlos; Si el dispositivo seleccionado se desconecta, el complemento vuelve automáticamente al valor predeterminado del sistema y anuncia el cambio. Activo solo cuando se utiliza el BASS backend. |
| Volumen | Establece el volumen cuando se inicia el complemento (0–200). Los cambios realizados durante la reproducción con `Ctrl+Win+↑` / `Ctrl+Win+↓` también se reflejan aquí. |
| Efecto de audio predeterminado | Establece el efecto de audio aplicado cuando se inicia NVDA o una estación comienza a reproducirse. El efecto seleccionado corresponde a la lista de efectos en el navegador de estaciones. Activo solo cuando se utiliza el BASS backend. |
| Ganancia de EQ (Bass / Treble / Vocal) | Establece el nivel de ganancia en dB para cada banda de EQ (−15 a +15). Estos valores se aplican cuando el efecto EQ correspondiente está activo y se guardan globalmente. Las reemplazos por estación se pueden almacenar utilizando el botón **Guardar perfil de audio** en la pestaña Favoritos. Activo solo cuando se utiliza el BASS backend. |
| Transición de cambio de estación(BASS backend) | Controla el comportamiento de transición al conmutar entre las estaciones. **Corte instantáneo** (por defecto) detiene la estación anterior justo antes de que comience la nueva. **Fundido encadenado corto (1 segundo)** y **Fundido encadenado normal (2 segundos)** inicia inmediatamente la nueva estación sin interrupción, luego desaparece gradualmente la estación anterior en segundo plano una vez confirmado el nuevo flujo activo. No tiene ningún efecto ni impacto en el rendimiento cuando se establece en Corte instantáneo. Solo disponible cuando el BASS backend está en uso. |
| Reanudar la última estación al iniciar NVDA | Cuando está habilitado, la última estación escuchada se reinicia automáticamente cada vez que se inicia NVDA. |
| Anunciar automáticamente los cambios de pista (metadatos ICY) | Cuando está habilitado, NVDA lee automáticamente el nombre de la nueva pista cada vez que cambia en una estación que transmite metadatos ICY. La primera canción también se anuncia inmediatamente al cambiar a una nueva estación. Deshabilitado por defecto. |
| Silenciar notificaciones | Cuando está habilitado, NVDA no anuncia cambios de estación, cambios de estado de reproducción (reproducir, pausar, detener) o eventos de grabación (iniciado, detenido, terminado). Mensajes de error, comentarios sobre favoritos, resultados de reconocimiento de música y notificaciones de las actualizaciones no se ven afectadas. También se puede activar sobre la marcha mediante un gesto de entrada no asignado. Deshabilitado por defecto. |
| Activar búfer de desplazamiento temporal (rebobinar radio en directo, ~10 minutos) | Activa o desactiva los controles de rebobinado `Ctrl+Win+J`/`Ctrl+Win+K`) y aumenta la captura en segundo plano de ~45 segundos a ~10 minutos. Una pequeña captura en segundo plano de la emisora ​​en reproducción siempre se ejecuta, incluso cuando está deshabilitada — consulta la nota en la sección **Desplazamiento temporal (rebobinar radio en directo)** a continuación. También se puede alternar al instante con `Ctrl+Win+T`. Requiere el BASS backend. Deshabilitado por defecto — consulta la sección **Desplazamiento temporal (rebobinar radio en directo)** a continuación para obtener más detalles. |
| Guardar las canciones favoritas en un archivo de texto | Cuando está habilitado, la información de la pista se copia al portapapeles pulsando `Ctrl+Win+I` tres veces y también se añade a `Documentos\FreeRadio Recordings\likedSongs.txt`. Si no hay metadatos ICY disponibles, el resultado del reconocimiento de Shazam se guarda en el mismo archivo. Deshabilitado por defecto. |
| Cuando Ctrl+Win+P se pulsa sin reproducción activa | Determina qué sucede cuando se pulsa este atajo y no hay nada  en reproducción: iniciar la última estación o abrir la lista de favoritos. |
| Cuando Ctrl+Win+P se pulsa dos veces | Selecciona lo que sucede cuando se pulsa el atajo dos veces en sucesión rápida: no hacer nada, abrir la lista de favoritos, abrir la pestaña de grabación o abrir la pestaña del temporizador. Cuando "No hacer nada" es seleccionado, la primera pulsación responde instantáneamente sin demora. |
| Cuando Ctrl+Win+P se pulsa tres veces | Selecciona lo que sucede cuando se pulsa el atajo tres veces en sucesión rápida: no hacer nada, abrir la lista de favoritos, abrir búsqueda de emisoras, abrir la pestaña de grabación o abrir la pestaña del temporizador. |
| Buscar actualizaciones automáticamente al iniciar | Cuando está habilitado, una verificación de actualización en segundo plano se ejecuta cada vez que se inicia NVDA; se le notificará si se encuentra una nueva versión. Cuando está deshabilitado, los controles automáticos se detienen pero los controles manuales permanecen disponibles. |
| Ruta ffmpeg.exe | Ruta de acceso al ffmpeg.exe usado para el reconocimiento de música. Si se deja vacío, un ffmpeg.exe en la carpeta del complementos se usa automáticamente. |
| Ruta VLC | Si VLC no está instalado o se encuentra en una ubicación no estándar, aquí se puede ingresar la ruta completa al ejecutable. |
| Ruta wmplayer.exe | Ingrese la ruta a Windows Media Player aquí si es necesario. |
| Ruta PotPlayer | Si PotPlayer se encuentra en una ubicación no estándar, su ruta se puede ingresar aquí. |
| Carpeta de grabaciones | Establece la carpeta donde se guardan los archivos grabados. Si se deja en blanco, la ubicación predeterminada `Documentos\FreeRadio Recordings\` se utiliza. Un botón Explorar carpeta le permite seleccionar la carpeta de forma interactiva. Los cambios entran en vigor inmediatamente después de guardarlos. |
| Desactivar la verificación de conectividad a Internet antes de reproducir | Recomendado para usuarios que experimentan un retraso antes de que una estación comience a reproducirse. También es útil cuando el DNS está bloqueado. |

## Silenciar Notificaciones

Cuando **Silenciar notificaciones** está habilitado en las Opciones, NVDA silencia los siguientes anuncios automáticos:

- Nombre de la estación cuando comienza a reproducirse una nueva estación
- Cambios de estado de reproducción: reproducir, pausar, detener
- Eventos de grabación: iniciado, detenido, terminado (grabaciones instantáneas, de canciones y programadas)
- Anuncios de cambio de pista ICY, incluso cuando **Anunciar automáticamente los cambios de pista**   también está habilitado

Los siguientes anuncios **no** se ven afectados intencionalmente: mensajes de error, comentarios sobre favoritos (añadido / ya en la lista), resultados de reconocimiento de música y notificaciones de actualización.

La configuración se puede alternar desde el Menú NVDA → Preferencias → Opciones → FreeRadio, o instantáneamente en cualquier momento mediante un gesto de entrada no asignado (asignar uno desde el Menú NVDA → Preferencias → Gestos de Entrada → FreeRadio). Cuando está habilitado, NVDA anuncia una vez "Notificaciones silenciadas" o "Notificaciones reactivadas" para confirmar el cambio.

## Anunciar automáticamente los cambios de pista

Cuando la opción **Anunciar automáticamente los cambios de pista** se activa en las Opciones, FreeRadio comprueba el flujo de metadatos ICY de la estación activa en segundo plano aproximadamente cada 5 segundos. Cuando cambia la pista, NVDA lee automáticamente el nuevo título; no es necesario pulsar ninguna tecla.

Al cambiar a una nueva emisora, la información de la primera pista se anuncia tan pronto como se establece la conexión. Si cambia a una estación que no transmite metadatos ICY, el sistema permanece en silencio y la información de la pista de la estación anterior no se repite.

Esta función está desactivada de forma predeterminada y se puede alternar desde el Menú NVDA → Preferencias → Opciones → FreeRadio.

## Canciones favoritas

Cuando la opción **Guardar las canciones favoritas en un archivo de texto** está activado, la información de la pista se copia al portapapeles pulsando tres veces `Ctrl+Win+I` también se añade línea por línea a `Documentos\FreeRadio Recordings\likedSongs.txt`.

En las estaciones que transmiten metadatos ICY, el título de la pista y el artista se guardan directamente. En las estaciones sin metadatos ICY, el resultado del reconocimiento de Shazam se guarda en el mismo archivo; ambas fuentes comparten la misma lista. El archivo se crea automáticamente si no existe; cada entrada se añade al final del archivo y las entradas anteriores nunca se eliminan.

## Pestaña de Canciones favoritas

La pestaña **Canciones favoritas** en el navegador de estaciones se muestran todas las pistas guardadas en `likedSongs.txt`. La lista se recarga automáticamente desde el archivo cada vez que se abre la pestaña.

Un campo **Filtrar** encima de la lista permite limitar las pistas mostradas en tiempo real. Escribe cualquier parte del título de una canción o nombre del artista y la lista se actualiza instantáneamente a cada pulsación. NVDA anuncia el número de resultados coincidentes tras cada cambio. Pulsa la flecha `Abajo` desde el campo Filtrar para mover el foco directamente a la lista.

Seleccionar una pista de la lista permite las siguientes acciones:

- **Reproducir en Spotify:** Intenta abrir la aplicación de escritorio de Spotify directamente. Si la aplicación no está instalada, vuelve al sitio web de Spotify y automáticamente comienza a reproducir el primer resultado.
- **Reproducir en YouTube (`Alt+O`):** Busca en YouTube la pista seleccionada y abre los resultados en el navegador predeterminado.
- **Mostrar letra:** Obtiene y muestra la letra de la pista seleccionada. Las letras se obtienen de [lrclib.net](https://lrclib.net) (gratuito, sin cuenta requerida). Se anuncia un breve mensaje "Obteniendo letra…" mientras la búsqueda se ejecuta en segundo plano. Si se encuentran letras, se abren en un cuadro de diálogo de solo lectura donde puedes leerlas con NVDA y copiarlas al portapapeles. Si no se encuentran letras, NVDA lo anuncia. El botón se desactiva temporalmente mientras se realiza una búsqueda para evitar solicitudes duplicadas.
- **Eliminar (`Alt+M`):** Elimina la pista seleccionada de `likedSongs.txt` y  actualiza la lista. La tecla `Suprimir` también activa este botón cuando la lista está enfocada.
- **Refrescar (`Alt+E`):** Vuelve a cargar la lista desde el archivo.

Los botones Spotify, YouTube, Mostrar letra y Eliminar sólo se activan cuando se selecciona una pista real en la lista.

### Servicio de letras

FreeRadio usa [lrclib.net](https://lrclib.net) para obtener letras — una base de datos gratuita y abierta que no requiere clave de API ni cuenta. El proceso de búsqueda analiza la cadena de pista almacenada en `likedSongs.txt` y prueba consultas progresivamente más amplias hasta encontrar letras:

1. Coincidencia exacta con el nombre completo del artista y el título limpio (los sufijos de ruido como "Remastered", "Live" o etiquetas de año se eliminan antes de buscar).
2. Coincidencia exacta con el nombre completo del artista y el título original (si la limpieza lo cambió).
3. Coincidencia exacta con solo el primer nombre de artista y el título limpio (para cadenas de múltiples artistas como "Artista A & Artista B").
4. Búsqueda difusa con el primer nombre de artista y el título limpio.
5. Búsqueda difusa con la cadena de pista sin procesar como último recurso.

Cuando hay letras en texto plano disponibles, se muestran tal cual. Cuando solo hay letras LRC sincronizadas por tiempo, se eliminan las marcas de tiempo y se muestra el texto plano. Las pistas instrumentales se reportan como no encontradas.

## Reproducción

El complemento selecciona un backend de reproducción usando el siguiente orden de prioridad:

1. **BASS** — el backend predeterminado y principal. No se requiere instalación por separado; viene incluido con el complemento. BASS envía el audio directamente a la pila de audio de Windows y aparece en el mezclador de volumen de Windows como una fuente de audio independiente llamada "pythonw.exe", separada de NVDA. Esto significa que el audio de FreeRadio circula en un canal completamente separado del habla de NVDA: la radio no se corta, no se mezcla ni se ve afectada por la propia configuración de audio de NVDA mientras NVDA está hablando. El usuario puede ajustar el volumen de la radio independientemente de NVDA en el Mezclador de volumen de Windows. Admite HTTP, HTTPS y la mayoría de los formatos de flujo integrados. La puesta en espejo  de audio solo está disponible con este backend.
2. **VLC** — se hace cargo si el BASS falla. Se busca automáticamente en ubicaciones de instalación comunes, carpetas de perfil de usuario y la RUTA del sistema.
3. **PotPlayer** — probado si no se encuentra VLC. Se busca automáticamente en ubicaciones de instalación comunes.
4. **Windows Media Player** — utilizado como último recurso; requiere que el componente WMP esté instalado en el sistema.

## Comprobación de Actualización

FreeRadio busca automáticamente nuevas versiones a través de GitHub.

**Comprobación automática:** Se ejecuta silenciosamente en segundo plano 15 segundos después de que se inicia NVDA. Si se encuentra una nueva versión, se le notificará; si no se encuentra ninguno, no se muestra ningún mensaje.

**Comprobación manual:** Se puede activar a solicitud desde Herramientas NVDA → FreeRadio → **Buscar actualizaciones…**. Cuando se inicia de esta manera, el resultado se anuncia incluso si la versión está actualizada.

**Cuando se encuentra una actualización:** Se abre un cuadro de diálogo que muestra el número de versión y la versión instalada.

- Si hay un archivo `.nvda-addon` directamente descargable disponible en la release de GitHub, se muestra un botón **Descargar y Instalar**. Una vez confirmado, el archivo se descarga en segundo plano, NVDA anuncia cuándo comienza la descarga y La propia pantalla de instalación se abre automáticamente.
- Si no hay ningún enlace de descarga directa disponible,, un botón **Abrir la página** se muestra y la página de la release en GitHub se abre en el navegador predeterminado.

**Para desactivar las comprobaciones automáticas:** Deshabilitar la opción **Buscar actualizaciones automáticamente al iniciar** desde el Menú NVDA → Preferencias → Opciones → FreeRadio.

## Licencia

GPL v2