"use strict";

// side navigation bar
function toggleSidebar() {
  document.getElementById("side-nav").classList.toggle("toggle-active");
  document.getElementById("main").classList.toggle("toggle-active");
  document.getElementById("top-navbar").classList.toggle("toggle-active");
  document.querySelector(".manage-wrap").classList.toggle("toggle-active");
}

// #################################
// popup

var c = 0;
function pop() {
  if (c == 0) {
    document.getElementById("popup-box").style.display = "block";
    c = 1;
  } else {
    document.getElementById("popup-box").style.display = "none";
    c = 0;
  }
}

// const popupMessagesButtons = document.querySelectorAll('popup-btn-messages')

// popupMessagesButtons.forEach(button, () => {
//     button.addEventListener('click', () => {
//         document.getElementById('popup-box-messages').style.display = 'none';
//     })
// })

// const popupMessagesButtom = document.getElementById('popup-btn-messages')
// popupMessagesButtom.addEventListener('click', () => {
//     document.getElementById('popup-box-messages').style.display = 'none';
// })
// ##################################

// Example starter JavaScript for disabling form submissions if there are invalid fields
// Fetch all the forms we want to apply custom Bootstrap validation styles to
var forms = document.getElementsByClassName("needs-validation");

// Loop over them and prevent submission
Array.prototype.filter.call(forms, function (form) {
  form.addEventListener(
    "submit",
    function (event) {
      if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false
  );
});
// ##################################

// extend and collapse
function showCourses(btn) {
  var btn = $(btn);

  if (collapsed) {
    btn.html('Collapse <i class="fas fa-angle-up"></i>');
    $(".hide").css("max-height", "unset");
    $(".white-shadow").css({ background: "unset", "z-index": "0" });
  } else {
    btn.html('Expand <i class="fas fa-angle-down"></i>');
    $(".hide").css("max-height", "150");
    $(".white-shadow").css({
      background: "linear-gradient(transparent 50%, rgba(255,255,255,.8) 80%)",
      "z-index": "2",
    });
  }
  collapsed = !collapsed;
}

$(document).ready(function () {
  $("#primary-search").focus(function () {
    $("#top-navbar").attr("class", "dim");
    $("#side-nav").css("pointer-events", "none");
    $("#main-content").css("pointer-events", "none");
  });
  $("#primary-search").focusout(function () {
    $("#top-navbar").removeAttr("class");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  });
});

// Sidebar con overlay para móvil (definitivo)
function openSidebar() {
  document.getElementById("side-nav").classList.add("toggle-active");
  document.getElementById("main").classList.add("toggle-active");
  document.getElementById("top-navbar").classList.add("toggle-active");
  document.querySelector(".manage-wrap").classList.add("toggle-active");
  // Eliminar overlay anterior si existe
  var oldOverlay = document.getElementById('sidebar-overlay');
  if (oldOverlay) oldOverlay.remove();
  // Crear overlay y ponerlo al final del body
  var overlay = document.createElement('div');
  overlay.id = 'sidebar-overlay';
  overlay.onclick = closeSidebar;
  document.body.appendChild(overlay);
}

function closeSidebar() {
  document.getElementById("side-nav").classList.remove("toggle-active");
  document.getElementById("main").classList.remove("toggle-active");
  document.getElementById("top-navbar").classList.remove("toggle-active");
  document.querySelector(".manage-wrap").classList.remove("toggle-active");
  var overlay = document.getElementById('sidebar-overlay');
  if (overlay) overlay.remove();
}

document.addEventListener('DOMContentLoaded', function () {
  console.log('=== DOMContentLoaded iniciado ===');
  console.log('Verificando elementos del formulario...');

  var btn = document.getElementById('sidebar-toggle-btn');
  if (btn) {
    btn.onclick = function () {
      if (document.getElementById("side-nav").classList.contains("toggle-active")) {
        closeSidebar();
      } else {
        openSidebar();
      }
    };
  }
  // Permitir cerrar sidebar con tecla ESC
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeSidebar();
    }
  });
  // Cerrar sidebar si se hace scroll en móvil
  window.addEventListener('scroll', function () {
    if (window.innerWidth <= 900 && document.getElementById("side-nav").classList.contains("toggle-active")) {
      closeSidebar();
    }
  });

  // Lógica de forma de pago en cotización
  console.log('Iniciando lógica de forma de pago...');
  actualizarCamposPago();

  // Event listeners para forma de pago
  var formaPago = document.getElementById('id_forma_pago');
  var tipoPlazoSelect = document.getElementById('tipo-plazo-select');
  var plazoDiasInput = document.getElementById('id_plazo_credito_dias');
  var plazoFechaInput = document.getElementById('id_plazo_credito_fecha');

  if (formaPago) {
    console.log('Agregando event listener a formaPago');
    formaPago.addEventListener('change', actualizarCamposPago);
  } else {
    console.log('ERROR: No se encontró el elemento formaPago para agregar event listener');
  }

  if (tipoPlazoSelect) {
    console.log('Agregando event listener a tipoPlazoSelect');
    tipoPlazoSelect.addEventListener('change', actualizarCamposPago);
  }

  if (plazoDiasInput) {
    plazoDiasInput.addEventListener('input', actualizarCamposPago);
  }
  if (plazoFechaInput) {
    plazoFechaInput.addEventListener('change', actualizarCamposPago);
  }
});

// Lógica de forma de pago en cotización
function actualizarCamposPago() {
  var formaPago = document.getElementById('id_forma_pago');
  var tipoPlazoGroup = document.getElementById('tipo-plazo-group');
  var tipoPlazoSelect = document.getElementById('tipo-plazo-select');
  var plazoDiasGroup = document.getElementById('plazo-credito-dias-group');
  var plazoFechaGroup = document.getElementById('plazo-credito-fecha-group');
  var plazoCreditoText = document.getElementById('plazo-credito-text');
  var plazoDiasInput = document.getElementById('id_plazo_credito_dias');
  var plazoFechaInput = document.getElementById('id_plazo_credito_fecha');
  var adelantoText = document.getElementById('adelanto-text');
  var saldoText = document.getElementById('saldo-text');
  var porcentajeAdelantoText = document.getElementById('porcentaje-adelanto-text');
  var porcentajeSaldoText = document.getElementById('porcentaje-saldo-text');

  // Obtener el monto final (total + IGV + detracción)
  function getMontoFinal() {
    var monto = 0;
    var el = document.getElementById('total-final');
    if (el) {
      monto = parseFloat(el.textContent.replace('S/ ', '').replace(',', '.')) || 0;
    }
    return monto;
  }

  // Ocultar todo por defecto
  if (tipoPlazoGroup) tipoPlazoGroup.style.display = 'none';
  if (plazoDiasGroup) plazoDiasGroup.classList.add('d-none');
  if (plazoFechaGroup) plazoFechaGroup.classList.add('d-none');

  // Mostrar selector y campo según selección
  if (formaPago && formaPago.value === 'al_credito') {
    if (tipoPlazoGroup) tipoPlazoGroup.style.display = '';
    if (tipoPlazoSelect) {
      if (tipoPlazoSelect.value === 'dias' && plazoDiasGroup) {
        plazoDiasGroup.classList.remove('d-none');
      } else if (tipoPlazoSelect.value === 'fecha' && plazoFechaGroup) {
        plazoFechaGroup.classList.remove('d-none');
      }
    }
  }

  // Actualizar resumen de plazo de crédito
  if (plazoCreditoText) {
    if (formaPago && formaPago.value === 'al_credito') {
      if (tipoPlazoSelect.value === 'dias' && plazoDiasInput && plazoDiasInput.value) {
        plazoCreditoText.textContent = plazoDiasInput.value + ' días desde la cotización';
      } else if (tipoPlazoSelect.value === 'fecha' && plazoFechaInput && plazoFechaInput.value) {
        plazoCreditoText.textContent = 'Hasta el ' + plazoFechaInput.value;
      } else {
        plazoCreditoText.textContent = 'Selecciona el tipo de plazo';
      }
    } else {
      plazoCreditoText.textContent = '-';
    }
  }

  // Calcular y mostrar adelanto, saldo y porcentajes
  var montoFinal = getMontoFinal();
  var adelanto = 0, saldo = 0, adelantoPct = 0, saldoPct = 0;
  if (formaPago) {
    if (formaPago.value === '50_50') {
      adelanto = montoFinal * 0.5;
      saldo = montoFinal * 0.5;
      adelantoPct = 50;
      saldoPct = 50;
    } else if (formaPago.value === '100_adelantado') {
      adelanto = montoFinal;
      saldo = 0;
      adelantoPct = 100;
      saldoPct = 0;
    } else if (formaPago.value === 'al_credito') {
      adelanto = 0;
      saldo = montoFinal;
      adelantoPct = 0;
      saldoPct = 100;
    }
  }
  if (adelantoText) adelantoText.textContent = adelanto.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' }) + (adelanto === 0 ? ' (Sin adelanto)' : '');
  if (saldoText) saldoText.textContent = saldo.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' }) + (formaPago && formaPago.value === 'al_credito' ? ' (Total a crédito)' : '');
  if (porcentajeAdelantoText) porcentajeAdelantoText.textContent = adelantoPct + '%';
  if (porcentajeSaldoText) porcentajeSaldoText.textContent = saldoPct + '%';
}

// Función auxiliar para mostrar un elemento Bootstrap
function mostrarElementoBootstrap(elemento) {
  if (!elemento) return;
  elemento.classList.remove('d-none');
}
// Función auxiliar para ocultar un elemento Bootstrap
function ocultarElementoBootstrap(elemento) {
  if (!elemento) return;
  elemento.classList.add('d-none');
}

// Función para manejar el cambio de tipo de plazo
function actualizarTipoPlazo() {
  console.log('=== ACTUALIZANDO TIPO DE PLAZO ===');

  var tipoPlazoSelect = document.getElementById('tipo-plazo-select');
  var plazoDiasGroup = document.getElementById('plazo-credito-dias-group');
  var plazoFechaGroup = document.getElementById('plazo-credito-fecha-group');
  var plazoCreditoText = document.getElementById('plazo-credito-text');

  if (!tipoPlazoSelect) {
    console.log('ERROR: No se encontró tipoPlazoSelect');
    return;
  }

  console.log('Tipo de plazo seleccionado:', tipoPlazoSelect.value);

  // Ocultar ambos campos primero
  ocultarElementoBootstrap(plazoDiasGroup);
  ocultarElementoBootstrap(plazoFechaGroup);

  if (tipoPlazoSelect.value === 'dias') {
    console.log('Mostrando campo de días');
    mostrarElementoBootstrap(plazoDiasGroup);
    console.log('Campo de días mostrado correctamente');
  } else if (tipoPlazoSelect.value === 'fecha') {
    console.log('Mostrando campo de fecha');
    mostrarElementoBootstrap(plazoFechaGroup);
    console.log('Campo de fecha mostrado correctamente');
  } else {
    console.log('Ningún tipo seleccionado, ocultando ambos campos');
  }
  // Actualizar el resumen después de mostrar el campo
  actualizarCamposPago();
}

function actualizarResumenCredito() {
  var montoPagadoInput = document.getElementById('id_monto_cancelado');
  var montoPagadoResumen = document.getElementById('monto-pagado-resumen');
  var montoPendienteResumen = document.getElementById('monto-pendiente-resumen');
  var porcentajePagadoResumen = document.getElementById('porcentaje-pagado-resumen');
  var estadoCreditoResumen = document.getElementById('estado-credito-resumen');
  var totalFinalEl = document.getElementById('total-final');

  var montoPagado = parseFloat(montoPagadoInput ? montoPagadoInput.value : 0) || 0;
  var totalFinal = parseFloat(totalFinalEl ? totalFinalEl.textContent.replace('S/ ', '').replace(',', '.') : 0) || 0;
  var pendiente = totalFinal - montoPagado;
  var porcentaje = totalFinal > 0 ? (montoPagado / totalFinal) * 100 : 0;
  var estado = '-';
  if (montoPagado === 0) {
    estado = 'Pendiente';
  } else if (pendiente <= 0) {
    estado = 'Pagado';
  } else {
    estado = 'Pago Parcial';
  }

  if (montoPagadoResumen) montoPagadoResumen.textContent = montoPagado.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' });
  if (montoPendienteResumen) montoPendienteResumen.textContent = pendiente.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' });
  if (porcentajePagadoResumen) porcentajePagadoResumen.textContent = porcentaje.toFixed(1) + '%';
  if (estadoCreditoResumen) estadoCreditoResumen.textContent = estado;
}

document.addEventListener('DOMContentLoaded', function () {
  var montoPagadoInput = document.getElementById('id_monto_cancelado');
  if (montoPagadoInput) {
    montoPagadoInput.addEventListener('input', actualizarResumenCredito);
    actualizarResumenCredito();
  }
});
