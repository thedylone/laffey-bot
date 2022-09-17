function autocomplete(input, arr) {
    input.on("input", function (e) {
        inputText = this.value;
        $("#autocomplete-list").empty();
        var displayed = [];
        arr.forEach(a => {
            var group = $("#" + a);
            if (a.toLowerCase().includes(inputText.toLowerCase())) {
                group.css("display", "block");
                displayed.push(a);
            } else {
                group.css("display", "none");
                group.css("animation", 'none');
            }
        });
        if (inputText) {
            displayed.forEach(a => {
                $("#autocomplete-list")
                    .append($("<a></a>")
                        .attr("class", "autocomplete-item js-anchor")
                        .attr("href", "#" + a)
                        .html(a)
                        .on("click", function () {var e; if (location.pathname.replace(/^\//, "") === this.pathname.replace(/^\//, "") && location.hostname === this.hostname && (e = (e = $(this.hash)).length ? e : $("[name=" + this.hash.slice(1) + "]")).length) return $("html,body").animate({scrollTop: e.offset().top - $('.first-nav').height() - $(".js-nav").show().height()}, 1000), !1;})
                    );
            });
            $("#autocomplete-list").css("display", "inline-block");
            if (displayed.length == 0) {
                $("#autocomplete-list").append($("<a></a>")
                    .attr("class", "autocomplete-item")
                    .html("no results found")
                );
            }
        } else {
            $("#autocomplete-list").hide();
        }
        scrollanimate();
    });
}

function searchAnchor() {
    $(".search-anchor").on("click", function (e) {
        $($(this).attr('href')).show();
    });
}

function scrollanimate() {
    $(".animate__animated").each(function () {
        z = $(this).offset().top, o = $(window).height(), y = $(this).height(), t = $(window).scrollTop();
        if (z - 0.8 * o <= t && t < z + y) {
            window.matchMedia("(max-width: 800px)").matches ? w = '0s' : w = $(this).attr("animation-delay");
            $(this).css("animation", $(this).attr("animation-style") + " " + $(this).attr("animation-duration") + " forwards " + w + " ease-in-out");
        }
    });
}

function discordTime() {
    var time = new Date();
    var currentTime = time.toLocaleString('en-US', {hour: 'numeric', minute: 'numeric', hour12: true});
    document.querySelectorAll(".discord-message-timestamp, .discord-inline-timestamp").forEach(timestamp => {
        timestamp.innerHTML = "Today at " + currentTime;
    });
    document.querySelectorAll(".discord-hidden-timestamp").forEach(timestamp => {
        timestamp.innerHTML = currentTime;
    });
}

function openModal(modal, src = null) {
    modal.css("display", "flex");
    if (src != null) {
        $(modal).find("img").attr("src", src);
    }
    const body = document.body;
    body.style.top = -1 * window.pageYOffset + 'px';
    body.style.position = 'fixed';
}

function imagesOpenModal() {
    imgs = $(".discord-section img");
    for (var img of imgs) {
        $(img).on("click", (e) => {
            src = e.target.getAttribute("src");
            openModal($("#modal-image"), src);
        });
    }
}