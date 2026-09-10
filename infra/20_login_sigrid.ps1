# infra/20_login_sigrid.ps1
<#
.SYNOPSIS
    Comprueba, SOLO LEYENDO, si el login del ERP que este servicio derivaria de
    un correo existe de verdad en el maestro de usuarios de Sigrid. Dice si la
    siembra automatica va a funcionar para esa persona, o no.

.DESCRIPTION
    LA CONVENCION NO SE CUMPLE SIEMPRE, Y ESO ESTA MEDIDO. El servicio deriva
    un login CANDIDATO de la parte anterior a la arroba del correo, en
    minusculas, y lo verifica contra el ERP por lectura antes de firmar nada
    (F-009 R30, R31). Pero de los 8 usuarios del ERP con correo registrado,
    solo 6 cumplen esa convencion -el dato esta en la docstring de
    `derivar_login_candidato`, en `domain/models/cierre.py`-. Y hay un caso
    conocido: una persona de Posventa cuyo login del ERP es mas corto que el
    prefijo de su correo.

    Un 75 % no vale cuando el error consiste en que alguien recorra el circuito
    entero, llegue al cierre y se lo rechace un 409 que nadie esperaba. Este
    script permite saberlo ANTES, de una persona concreta y en un segundo.

    QUE HACE, EXACTAMENTE:

      1. Deriva el candidato del `-Correo`, igual que el dominio: se recorta,
         se pasa a minusculas y se toma lo que hay antes de la PRIMERA arroba.
         Con `-Login` se salta ese paso y se comprueba el que se le diga: es la
         via para los que NO siguen la convencion.
      2. Pregunta al ERP cuantas veces existe ese login, con LA MISMA CONSULTA
         que usa el servicio (`SQL_USUARIO` de
         `infrastructure/sigrid/consultas.py`). No hay SQL nuevo aqui: una
         consulta parecida daria un veredicto sobre algo que no es lo que va a
         pasar en el cierre.
      3. Da un veredicto de TRES casos, no de dos:
           - existe UNA vez  -> la siembra automatica funcionara.
           - NO existe       -> hay que dar de alta la correspondencia A MANO
                                con `infra/07_alta_usuario_sigrid.ps1`. Lo que
                                toca no es reintentar.
           - existe VARIAS   -> es una ambiguedad y hay que decidir cual. No se
                                elige por nuestra cuenta: firmar en el log de
                                un ERP de produccion en nombre de la persona
                                equivocada no se deshace solo.

    NO ESCRIBE NADA. Ni en Sigrid, ni en PostgreSQL, ni en Azure, ni en disco.
    La unica ruta que toca es `POST /api/sql/read`, que la pasarela sirve con
    un usuario SQL de solo lectura. La regla dura de `CLAUDE.md` es que en
    Sigrid solo se escribe desde el entorno desplegado, y esto lo lanza una
    persona desde su puesto. La correspondencia la escribe el script 07, que es
    otro y pide lo suyo.

    POR QUE ESTE NO CARGA `00_vars_postventa.ps1`. No toca ningun recurso de
    Azure de este proyecto: habla con la pasarela del ERP, que es de otro. Su
    fuente unica es `08_lectura_sigrid_comun.ps1` -la llamada HTTP, el manejo
    de la clave, los codigos de salida y el formato del veredicto-, igual que
    los scripts 09 a 17. Cargar ademas el fichero de nombres de recurso solo
    anadiria variables que no se usan.

    NINGUN VALOR EN ESTE FICHERO. Ni la raiz de la pasarela, ni la base, ni la
    clave, ni un correo, ni un login de nadie: el caso que no cumple la
    convencion se DESCRIBE, no se escribe. Este fichero SI se versiona.

.PARAMETER Correo
    El correo corporativo de la persona. De el se deriva el candidato. No se
    imprime entero: lo que se imprime es el candidato.

.PARAMETER Login
    Un login del ERP concreto, para comprobar directamente uno que no siga la
    convencion. Excluyente con `-Correo`.

.PARAMETER SigridBaseUrl
    La raiz de la pasarela. Si no se pasa, se toma de `$env:SIGRID_API_BASE_URL`.

.PARAMETER SigridBaseDatos
    La base de negocio del ERP. Si no se pasa, se toma de
    `$env:SIGRID_BASE_DATOS`.

.EXAMPLE
    # Lo normal: comprobar si la convencion vale para esa persona.
    powershell -ExecutionPolicy Bypass -File infra\20_login_sigrid.ps1 -Correo "<el correo de la persona>"

.EXAMPLE
    # Comprobar un login del ERP que NO sigue la convencion.
    powershell -ExecutionPolicy Bypass -File infra\20_login_sigrid.ps1 -Login "<el login del ERP>"
#>

[CmdletBinding()]
param(
    [string]$Correo,
    [string]$Login,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# La consulta del servicio, LITERAL. Es `SQL_USUARIO` de
# `infrastructure/sigrid/consultas.py`, y un test lo comprueba importandola:
# si alli cambiara y aqui no, este script estaria dando un veredicto sobre una
# pregunta que el servicio ya no hace.
#
# Va parametrizada con el marcador `?` (sigrid_api.md 5.2). Un login
# concatenado en la cadena seria una inyeccion contra el ERP de produccion
# lanzada desde un puesto de trabajo.
$SQL_USUARIO = 'SELECT COUNT(*) FROM dbo.usu WHERE cod = ?'


function Derivar-LoginCandidato {
    <#
    .SYNOPSIS
        El login que el servicio PROPONDRIA para ese correo (F-009 R30).

    .DESCRIPTION
        Traduccion literal de `derivar_login_candidato` de
        `domain/models/cierre.py`: se recorta, se pasa a minusculas y se toma
        lo que hay antes de la PRIMERA arroba. Sin arroba no hay candidato y
        se devuelve cadena vacia: aqui no se inventa nada.

        Derivarlo "parecido" produciria un veredicto sobre un login que el
        servicio nunca va a proponer, que es peor que no comprobar nada.
    #>
    param([string]$Correo)

    $limpio = ("" + $Correo).Trim().ToLower()
    $arroba = $limpio.IndexOf("@")
    if ($arroba -lt 1) { return "" }
    return $limpio.Substring(0, $arroba).Trim()
}


# --- Precondiciones ----------------------------------------------------------

$tieneCorreo = -not [string]::IsNullOrWhiteSpace($Correo)
$tieneLogin = -not [string]::IsNullOrWhiteSpace($Login)

if ($tieneCorreo -and $tieneLogin) {
    Salir-Con ("Se han pasado -Correo y -Login a la vez. Son excluyentes: o se " +
        "deriva el candidato del correo, o se comprueba el login que se diga.") $SALIDA_PARAMETRO
}
if (-not $tieneCorreo -and -not $tieneLogin) {
    Salir-Con ("Falta -Correo (para derivar el candidato como lo hace el " +
        "servicio) o -Login (para comprobar uno concreto).") $SALIDA_PARAMETRO
}

if ($tieneLogin) {
    $candidato = $Login.Trim()
    $origen = "-Login (tal cual, sin derivar)"
}
else {
    $candidato = Derivar-LoginCandidato -Correo $Correo
    $origen = "derivado del correo (parte anterior a la arroba, en minusculas)"
    if (-not $candidato) {
        Salir-Con ("De ese correo no sale ningun candidato: no tiene arroba, o " +
            "no tiene nada delante de ella. Si la persona existe en el ERP con " +
            "otro login, comprueba ese con -Login.") $SALIDA_PARAMETRO
    }
}

# El tope del campo del ERP, la misma comprobacion que hace el script 07: un
# login truncado es OTRO login, y lo que quedaria firmado en `dbo.log` es que
# cerro la incidencia alguien que no existe (F-009 R35).
if ($candidato.Length -gt 48) {
    Salir-Con ("Ese login no cabe en el campo del ERP, que admite 48 " +
        "caracteres. No se trunca.") $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Login del ERP para el cierre (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Candidato : $candidato"
Write-Host "  Origen    : $origen"
Write-Host ""


# --- La unica consulta, la del servicio -------------------------------------

$respuesta = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $SQL_USUARIO `
    -Parametros @($candidato) -MaxFilas 10

# La consulta devuelve UNA columna SIN NOMBRE -es un recuento-, asi que se lee
# por posicion y no con `Get-SigridValor`. Es la excepcion, y es segura porque
# la columna es una sola: ponerle un alias seria cambiar la consulta del
# servicio, que es justo lo que este script no puede hacer.
$veces = 0
if ($respuesta.row_count -ge 1) { $veces = [int]$respuesta.rows[0][0] }


# --- El veredicto, de tres casos --------------------------------------------

Reiniciar-Veredicto
Anotar -Que "login candidato" -Valor $candidato
Anotar -Que "veces que aparece en dbo.usu" -Valor $veces
Comprobar -Que "existe exactamente una vez (R30, R31)" -Esperado "1" -Obtenido "$veces"

if ($veces -eq 1) {
    Write-Host ("El ERP confirma el login. La siembra automatica funcionara " +
        "para esta persona: el servicio derivara este mismo candidato, lo " +
        "verificara y guardara la correspondencia solo.") -ForegroundColor Green
}
elseif ($veces -eq 0) {
    Write-Host "Ese login NO existe en el maestro de usuarios del ERP." -ForegroundColor Red
    Write-Host ""
    Write-Host ("Que hacer: dar de alta la correspondencia A MANO. No es un " +
        "fallo transitorio y reintentar no lo arregla:") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("  infra\07_alta_usuario_sigrid.ps1 -UsuarioOid <el oid de " +
        "Entra> -LoginSigrid <el login real del ERP>") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("El login real lo dice Posventa o el dueno del ERP. Si lo " +
        "sabes, compruebalo antes con -Login.") -ForegroundColor Yellow
}
elseif ($veces -gt 1) {
    Write-Host ("Ese login aparece $veces veces en el maestro de usuarios.") -ForegroundColor Red
    Write-Host ""
    Write-Host ("Que hacer: decidir CUAL con el dueno del ERP. No se elige por " +
        "nuestra cuenta: la fila de auditoria del cierre queda firmada con " +
        "ese login, y firmar en nombre de la persona equivocada no se deshace " +
        "solo.") -ForegroundColor Yellow
}

Write-Host ""
Escribir-Veredicto -Titulo "LOGIN DEL ERP"
