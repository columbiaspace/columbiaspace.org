$(document).ready(function() {

	var navOffset = $('.navbar').height();
	console.log(navOffset);

	$('body').scrollspy({
	   offset: navOffset
	});

	$('#aboutNav a').click(function(event) {
	    event.preventDefault();
	    $('html, body').animate({
            scrollTop: $(this.hash).offset().top - navOffset
        }, 600,'easeInOutQuart');
	    window.location.hash = $(this).attr('href');
	});

	$('#nav-logo a').click(function(event) {
	    event.preventDefault();
	    $('html, body').animate({
            scrollTop: "0px"
        }, 600,'easeInOutQuart');
	    window.location.hash = $(this).attr('href');
	});
});