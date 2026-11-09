$(document).ready(function() {
    $('a.abstract').click(function() {
        $(this).parent().parent().find(".abstract.hidden").toggleClass('open');
    });
    $('a.bibtex').click(function() {
        $(this).parent().parent().find(".bibtex.hidden").toggleClass('open');
    });
    $('a').removeClass('waves-effect waves-light');

    // news items past site.news_limit are rendered hidden; this reveals them
    $('.news-toggle').click(function() {
        var button = $(this);
        var hidden = button.closest('.news').find('tr.news-earlier');
        var expanded = hidden.first().is(':visible');
        hidden.prop('hidden', expanded);
        button.text(expanded ? button.data('more') : button.data('less'));
    });
});
