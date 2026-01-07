// (function($) {
//     'use strict';
    
//     $(document).ready(function() {
//         // Obtener los campos
//         var numeralField = $('#id_numeral');
//         var carpetaField = $('#id_carpeta');
        
//         if (numeralField.length && carpetaField.length) {
//             // Guardar todas las opciones originales de carpetas
//             var todasLasCarpetas = carpetaField.html();
//             var carpetasOriginales = [];
            
//             carpetaField.find('option').each(function() {
//                 var option = $(this);
//                 carpetasOriginales.push({
//                     value: option.val(),
//                     text: option.text(),
//                     numeral: option.attr('data-numeral')
//                 });
//             });
            
//             // Función para filtrar carpetas
//             function filtrarCarpetas() {
//                 var numeralSeleccionado = numeralField.val();
                
//                 if (!numeralSeleccionado) {
//                     // Si no hay numeral seleccionado, limpiar carpetas
//                     carpetaField.html('<option value="">---------</option>');
//                     carpetaField.prop('disabled', true);
//                     return;
//                 }
                
//                 // Habilitar el campo de carpetas
//                 carpetaField.prop('disabled', false);
                
//                 // Hacer petición AJAX para obtener carpetas del numeral
//                 $.ajax({
//                     url: '/admin/get-carpetas-por-numeral/',
//                     data: {
//                         'numeral_id': numeralSeleccionado,
//                         'app': window.location.pathname.split('/')[2] // transparencia, comude, etc.
//                     },
//                     dataType: 'json',
//                     success: function(data) {
//                         // Limpiar opciones actuales
//                         carpetaField.html('<option value="">---------</option>');
                        
//                         // Agregar las carpetas filtradas
//                         $.each(data.carpetas, function(index, carpeta) {
//                             carpetaField.append(
//                                 $('<option></option>')
//                                     .attr('value', carpeta.id)
//                                     .text(carpeta.ruta_completa)
//                             );
//                         });
                        
//                         // Si hay un valor previamente seleccionado, mantenerlo
//                         var valorActual = carpetaField.attr('data-selected');
//                         if (valorActual) {
//                             carpetaField.val(valorActual);
//                         }
//                     },
//                     error: function() {
//                         console.error('Error al cargar las carpetas');
//                     }
//                 });
//             }
            
//             // Ejecutar al cambiar el numeral
//             numeralField.on('change', filtrarCarpetas);
            
//             // Ejecutar al cargar la página (para edición)
//             if (numeralField.val()) {
//                 filtrarCarpetas();
//             } else {
//                 carpetaField.prop('disabled', true);
//             }
//         }
//     });
// })(django.jQuery);