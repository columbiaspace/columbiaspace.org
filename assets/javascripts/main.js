$(document).ready(function() {

	var navOffset = $('.navbar').height();
	var isDrake = false;
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

	$('#drakeme_button').click(function(event) {
		event.preventDefault();
		console.log("triggered");
		if(isDrake){
			$('html,body').removeClass('cursor');
			isDrake = false;
		}else{
			$('html,body').addClass('cursor');
			isDrake = true;
		}
		
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
