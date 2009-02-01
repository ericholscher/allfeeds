$(document).ready(function() {
    // Confirm language and template change if page is not saved
    var selects = ["language", "template"];
    var original_values = Array()
    $.each(selects, function(i, name){
        original_values[i] = $('#id_'+name)[0].selectedIndex;
        $('#id_'+name).change(function() {
            if (this.selectedIndex != original_values[i]) {
                var array = window.location.href.split('?');
                var query = $.query.set(name, this.options[this.selectedIndex].value).toString();
                var answer = confirm(gettext("Are you sure you want to change the "+name+" without saving the page first?"));
                if (answer) {
                    window.location.href = array[0]+query;
                } else {
                    this.selectedIndex = original_values[i];
                }
            }
        });
    });
    document.getElementById("id_title").focus();
    var template = $.query.get('template');
    if(template) {
        $('#id_template').find("option").each(function() {
            this.selected = false;
            if (template==this.value)
                this.selected = true;
        })
    }
    $("#id_slug").change(function() { this._changed = true; });
    $("#id_title").keyup(function() {
        var e = $("#id_slug")[0];
        if (!e._changed) {
            e.value = URLify(this.value, 64);
        }
    });
    $('#traduction-helper-select').change(function() {
        var index = this.selectedIndex;
        if(index == 0) {
            $('#traduction-helper-content').hide(); return;
        }
        var array = window.location.href.split('?');
        $.get(array[0]+'traduction/'+this.options[index].value+'/', function(html) {
            $('#traduction-helper-content').html(html);
            $('#traduction-helper-content').show();
        });
    });
    $('.revisions-list a').click( function() {
        var link = this;
        $.get(this.href, function(html) {
            $('a', $(link).parent().parent()).removeClass('selected');
            $(link).addClass('selected');
            var form_row = $(link).parents('.form-row')[0];
            if($('a.disable', form_row).length) {
                $('iframe', form_row)[0].contentWindow.document.getElementsByTagName("body")[0].innerHTML = html;
            } else {
                var formrow_textarea = $('textarea', form_row);
                formrow_textarea.attr('value', html);
                // support for WYMeditor
                if (WYMeditor) {
                    $(WYMeditor.INSTANCES).each(function(i, wym) {
                        if (formrow_textarea.attr('id') === wym._element.attr('id')) {
                            wym.html(html);
                        }
                    });
                }
            }
        });
        return false;
    });
});