$(document).ready(function() {

  // Chunky labels for radios & checkboxes

  if ($('form').length>0) {

    $(".block-label").each(function() {

      // Add focus
      $(".block-label input").focus(function() {
        $("label[for='" + this.id + "']").addClass("add-focus");
        }).blur(function() {
        $("label").removeClass("add-focus");
      });

      // Add selected class
      $('input:checked').parent().addClass('selected');

    });

    // Add/remove selected class
    $('.block-label').click(function() {

      $('input:not(:checked)').parent().removeClass('selected');
      $('input:checked').parent().addClass('selected');

      if ($(this).hasClass('selected')) {
        var target = $(this).attr('data-target');
        $('#'+target).show();
      }else {
        var target = $(this).attr('data-target');
        $('#'+target).hide();
      }


    });

    // For pre-checked inputs, show toggled content
    var target = $('input:checked').parent().attr('data-target');
    $('#'+target).show();

    }

});
