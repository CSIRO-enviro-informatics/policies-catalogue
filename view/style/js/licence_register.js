var rules = []

var updateRuleDisplay = function() {
    var ruleDisplay = $('#rule-list-template').clone()
    for (var i = 0; i < rules.length; i++) {
        for (var j = 0; j < rules[i]['ACTIONS'].length; j++){
            action = rules[i]['ACTIONS'][j]
            var template = $('#rule-item-template').clone().children()
            template.find('a').text(action['LABEL']).attr('href', action['LINK'])
            template.attr('data-rule-type', rules[i]['TYPE_URI'])
            template.attr('data-action-uri', action['URI'])
            if (rules[i]['ASSIGNORS'].length > 0)
                template.find('.assignors').removeAttr('hidden').text('Assignors: ' + rules[i]['ASSIGNORS'].join(', '))
            if (rules[i]['ASSIGNEES'].length > 0)
                template.find('.assignees').removeAttr('hidden').text('Assignees: ' + rules[i]['ASSIGNEES'].join(', '))
            template.insertBefore(ruleDisplay.find('.list-end-section[data-rule-type="' + rules[i]['TYPE_URI'] + '"]'))
        }
    }
    $('#rule-list').html(ruleDisplay.html())
    // Enable all bootstrap tooltips on page
    $('[data-toggle="tooltip"]').tooltip()
}

var updateActionDisplay = function(){
    $('.add-rule-modal').each(function(){
        var ruleType = $(this).attr('data-rule-type')
        var selectInputField = $(this).find('.action-select')
        selectInputField.children().each(function(){
            var action_uri = $(this).attr('data-action-uri')
            $(this).prop('hidden', false)
            for (var i = 0; i < rules.length; i++){
                for (var j = 0; j < rules[i]['ACTIONS'].length; j++){
                    action = rules[i]['ACTIONS'][j]
                    if (action['URI'] == action_uri
                    && (rules[i]['TYPE_URI'] == ruleType
                        || ruleType == 'http://www.w3.org/ns/odrl/2/prohibition'
                        || rules[i]['TYPE_URI'] == 'http://www.w3.org/ns/odrl/2/prohibition')){
                        $(this).prop('hidden', true)
                    }
                }
            }
        })
        selectInputField.val([])
        selectInputField.children().filter(function(){
            return $(this).css('display') != 'none'
        }).first().prop('selected', true)
    })
}

// Adds items to rule list
$('body').on('click', '.add-rule', function() {
    var modal = $(this).closest('.modal')
    var selectInputField = modal.find('.modal-body').find('select')
    var selectedAction = selectInputField.find('option:selected').first()
    var action = {
        'LABEL': selectedAction.text(),
        'URI': selectedAction.attr('data-action-uri'),
        'LINK': selectedAction.attr('data-action-link')
    }
    var assignors = []
    var assignees = []
    modal.find('.assignor-list').find('.list-group-item-label').each(function() {
        assignors.push($(this).text())
    })
    modal.find('.assignee-list').find('.list-group-item-label').each(function() {
        assignees.push($(this).text())
    })
    rules.push({
        'ACTIONS': [action],
        'TYPE_URI': modal.attr('data-rule-type'),
        'ASSIGNORS': assignors,
        'ASSIGNEES': assignees
    })
    updateRuleDisplay()
    updateActionDisplay()
    modal.find('.assignor-list').children(':not(".active")').remove()
    modal.find('.assignee-list').children(':not(".active")').remove()
})

// Removes items from rule list when X clicked
$('body').on('click', '.delete-rule-item', function() {
    var listItem = $(this).closest('li')
    var index = -1
    for (var i = 0; i < rules.length; i++) {
        for (var j = 0; j < rules[i]['ACTIONS'].length; j++){
            action = rules[i]['ACTIONS'][j]
            if (action['URI'] == listItem.attr('data-action-uri')
                && rules[i]['TYPE_URI'] == listItem.attr('data-rule-type'))
                index = i
        }
    }
    if (index == -1)
        throw "Cannot remove rule - rule index not found."
    rules.splice(index, 1)
    updateRuleDisplay()
    updateActionDisplay()
})

// AJAX request to get search results
$('body').on('click', '.search-button', function() {
    $.ajax({
        dataType: 'json',
        url: '/_search_results',
        data: {
            rules: JSON.stringify(rules),
        },
        success: function(data) {
            updateSearchResults(data['results'])
        }
    })
})

var updateSearchResults = function(results) {
    var resultsTemplate = $('#results-template').clone()
    if (results.length > 0) {
        resultsTemplate.find('#licences-found').removeAttr('hidden')
        for (var i = 0; i < results.length; i++){
            licence_entry = $('#licence-template').clone()
            licence_entry.find('.card-header').attr('data-target', '#licence-' + i).find('h5').text(results[i]['LABEL'])
            licence_entry.find('.collapse').attr('id', 'licence-' + i)
            licence_entry.find('a').attr('href', results[i]['LINK'])
            if (results[i]['EXTRA_RULES'].length > 0) {
                var header = licence_entry.find('.card-body').children('h5:eq(0)')
                var table = licence_entry.find('table:eq(0)')
                displayRulesForResult(header, table, results[i]['EXTRA_RULES'])
            }
            if (results[i]['MISSING_RULES'].length > 0) {
                var header = licence_entry.find('.card-body').children('h5:eq(1)')
                var table = licence_entry.find('table:eq(1)')
                displayRulesForResult(header, table, results[i]['MISSING_RULES'])
            }
            resultsTemplate.append(licence_entry.children())
        }
    }
    else
        resultsTemplate.find('#licences-not-found').removeAttr('hidden')
    $('#results').html(resultsTemplate.children())
}

var displayRulesForResult = function(header, table, rules){
    var permissions = []
    var duties = []
    var prohibitions = []
    for (var i = 0; i < rules.length; i++) {
        for (var j = 0; j < rules[i]['ACTIONS'].length; j++) {
           var action = rules[i]['ACTIONS'][j]
            switch (rules[i]['TYPE_URI']) {
                case 'http://www.w3.org/ns/odrl/2/permission':
                    permissions.push(action['LABEL'])
                    break
                case 'http://www.w3.org/ns/odrl/2/prohibition':
                    duties.push(action['LABEL'])
                    break
                case 'http://www.w3.org/ns/odrl/2/duty':
                    prohibitions.push(action['LABEL'])
                    break
            }
        }
    }
    header.prop('hidden', false)
    if (permissions.length > 0) {
        table.find('tr:eq(0)').prop('hidden', false)
        table.find('td:eq(0)').text(permissions.join(', '))
    }
    if (duties.length > 0) {
        table.find('tr:eq(1)').prop('hidden', false)
        table.find('td:eq(1)').text(duties.join(', '))
    }
    if (prohibitions.length > 0) {
        table.find('tr:eq(2)').prop('hidden', false)
        table.find('td:eq(2)').text(prohibitions.join(', '))
    }
}

//Moves to next step in form
$('body').on('click', '.previous-button', function() {
    $('.nav-link.active').parent().prev('li').find('a').trigger('click')
})
//Moves to previous step in form
$('body').on('click', '.next-button', function() {
    $('.nav-link.active').parent().next('li').find('a').trigger('click')
})

// Submits chosen rules with form
$('#licence-create-form').submit(function(event) {
    var rulesInput = $('<input>').attr('type', 'hidden').attr('name', 'rules').attr('class', 'hidden-rule-input').val(JSON.stringify(rules))
    $('#licence-create-form').append(rulesInput)
})

// Removing hidden inputs just in case the back button was used
$(window).on('unload', function() {
    $('.hidden-rule-input').remove()
})

// Adding assignors/assignees to a permission
$('body').on('click', '.add-party', function() {
    addParty($(this).parent().siblings('input').first())
})
$('body').on('focusout', '.party-input', function() {
    addParty($(this))
})
$('body').on('keyup', '.party-input', function(event) {
    if (event.keyCode === 13)
        addParty($(this))
})
var addParty = function(input_field) {
    if (input_field.val().length <= 0)
        return
    var isValid = input_field.closest('form').get(0).checkValidity()
    if (!isValid)
        return
    var party = input_field.val()
    input_field.val('')
    var new_list_item = $('#party-item-template').clone().children()
    new_list_item.find('div').text(party)
    input_field.closest('.input-group').prev().append(new_list_item)
}

$('.validate-party-form').submit(function(e){
    e.preventDefault()
})

// Removes assignor/assignee from a permission
$('body').on('click', '.delete-party-item', function() {
    $(this).parent().remove()
})

updateRuleDisplay()
// Enable all bootstrap tooltips on page
$('[data-toggle="tooltip"]').tooltip()