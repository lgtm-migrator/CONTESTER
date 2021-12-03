let codeMirrorConfig = {
    mode: "python", // Language mode
    theme: "material-palenight", // theme
    lineNumbers: true, // set number
    smartIndent: true, // smart indent
    indentUnit: 4, // Smart indent in 4 spaces
    indentWithTabs: true, // Smart indent with tabs
    lineWrapping: true, //
    // Add line number display, folder and syntax detector to the slot
    gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter", "CodeMirror-lint-markers"],
    foldGutter: true, // Enable code folding in slots
    autofocus: true, // Autofocus
    matchBrackets: true, // Match end symbols, such as "],}"
    autoCloseBrackets: true, // Auto close symbol
    styleActiveLine: true, // Display the style of the selected row
    scrollbarStyle: 'simple' // Scrollbar style
}

function loadCodeMirror(config) {
    // Configuring CodeMirror
    let editor = document.getElementById("editor__body");
    let myCodeMirror = CodeMirror(editor, config);

    // Loading code from local storage
    let codeMirrorText = localStorage.getItem('codeMirrorText');
    let initEditorValue;
    if (codeMirrorText) {
        initEditorValue = codeMirrorText
    } else {
        initEditorValue = ''
    }
    // Setting saved code
    myCodeMirror.setOption("value", initEditorValue);

    // Saving code everytime code changes
    myCodeMirror.on('change', function () {
        localStorage.setItem('codeMirrorText', myCodeMirror.getValue())
    })

    return myCodeMirror
}

myCodeMirror = loadCodeMirror(codeMirrorConfig)

// On click on submit button
$('#submit-code__btn').click(function () {
    let language = $('#dropdownMenuLanguage').find('.active')[0];
    let path = window.location.pathname.split('/')
    let request = {
        code: myCodeMirror.getValue(),
        lang: language.innerHTML,
        task: {
            grade: path[1],
            topic: path[2],
            task_number: path[3]
        }
    }

    // Sending AJAX response to server
    $.ajax({
        url: '/api/send_code',
        type: 'POST',
        async: true,
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify(request),
        // Before send
        beforeSend: function () {
            $('#code-response').html('');
        },
        // Everything OK
        success: function (response) {
            $('#code-response').replaceWith(response)
        },
        error: function () {
            console.log('Error')
        }
    })
})

// On dropdown child click do...
$(".dropdown-menu a").click(function () {
    // Remove any existing 'active' classes...
    $(this).closest('.dropdown-menu').find('a').removeClass('active');
    // Add 'active' class to clicked element...
    $(this).addClass('active');
});