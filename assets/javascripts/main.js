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

	$('#nav-index-logo a').click(function(event) {
	    event.preventDefault();
	    $('html, body').animate({
            scrollTop: "0px"
        }, 600,'easeInOutQuart');
	    window.location.hash = $(this).attr('href');
	});

	var input = document.querySelectorAll('input');
	for(i=0; i<input.length; i++){
		if(input[i].getAttribute('type') == "email"){
			input[i].setAttribute('size',input[i].getAttribute('placeholder').length + 1);
		}
	}

    $('#calendar').fullCalendar({
        googleCalendarApiKey: 'AIzaSyCrFoEKKvX6IgMKHETyyxbc6i4H5qvhaTs',
        events: {
            googleCalendarId: 'k1esjof3tmmr84i5um3812ni4s@group.calendar.google.com'
        }
    });
});
