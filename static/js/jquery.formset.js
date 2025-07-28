// static/js/jquery.formset.js
/**
 * jQuery Formset 1.2
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
;(function($) {
    $.fn.formset = function(opts)
    {
        var options = $.extend({}, $.fn.formset.defaults, opts);
        var $this = $(this);
        var $parent = $this.parent();
        var totalForms = $('#id_' + options.prefix + '-TOTAL_FORMS');
        var maxForms = $('#id_' + options.prefix + '-MAX_NUM_FORMS');
        var minForms = $('#id_' + options.prefix + '-MIN_NUM_FORMS');
        var insertBefore = options.addCssClass ? $this.find('.' + options.addCssClass) : options.addCssSelector ? $(options.addCssSelector) : $this;

        // Add button to add new form.
        $(options.addButton).click(function() {
            var currentForms = parseInt(totalForms.val());
            var numForms = currentForms;
            if (maxForms.val() != '' && maxForms.val() - currentForms <= 0) {
                return false;
            }
            var newForm = $(options.formTemplate.replace(/__prefix__/g, numForms));
            newForm.insertBefore(insertBefore);
            newForm.find('input, select, textarea').each(function() {
                var name = $(this).attr('name');
                if (name) {
                    $(this).attr('name', name.replace('-' + (numForms-1) + '-', '-' + numForms + '-'));
                    $(this).attr('id', $(this).attr('id').replace('-' + (numForms-1) + '-', '-' + numForms + '-'));
                }
            });
            totalForms.val(numForms + 1);
            // If a post-add callback was provided, call it with the new form.
            if (options.added) {
                options.added(newForm);
            }
            return false;
        });

        $this.each(function(i) {
            $(this).find(options.deleteCssClass).click(function() {
                var row = $(this).parents(options.formCssClass);
                row.remove();
                totalForms.val(parseInt(totalForms.val()) - 1);
                // If a post-delete callback was provided, call it with the deleted form.
                if (options.removed) {
                    options.removed(row);
                }
                return false;
            });
        });

        // Add a delete button to each form.
        $(this).find(options.formCssClass).each(function() {
            if ($(this).find(options.deleteCssClass).length == 0) {
                $(this).append('<a class="' + options.deleteCssClass.replace('.', '') + '" href="javascript:void(0)">' + options.deleteText + '</a>');
            }
        });

        // Cache the form template for later use.
        options.formTemplate = $(options.formCssClass + ':last').clone(true).get(0).outerHTML;

        return this;
    };

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        prefix: 'form',                  // The prefix for the formset
        formTemplate: null,              // The template for a new form (must be provided if not using formCssClass)
        addCssClass: 'add-row',          // CSS class applied to the add link
        deleteCssClass: 'delete-row',    // CSS class applied to the delete link
        addText: 'add another',          // Text for the add link
        deleteText: 'remove',            // Text for the delete link
        formCssClass: '.dynamic-form',   // CSS class applied to each form in a formset
        added: null,                     // Function to call after a form has been added
        removed: null                    // Function to call after a form has been deleted
    };
})(jQuery);
