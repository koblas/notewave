var next_page = "";

function auth_complete(service, error) {
    // Dialog callback will happen here
    var args = {
        site  : service,
        error : error || "",
        next  : next_page
    };
    $.getJSON('/openauth/connected', args, function (data) {
        _do_update(data.actions, null);
    });
}

function showMessage(t, message) {
    $("#notifyBar").remove();
    $.notifyBar({
        html: "<div style='width:100%; height: 100%; padding: 5px'>"+message+"</div>",
        cls: t + ' barmessage',
        delay: 3000,
        animationSpeed: "normal",
        barClass: "flash"
    });
};

/*****/
var $loading = $('<img src="/static/images/ajax-loader.gif" alt="loading"/>');

(function($) {
    var bound = false;

    $.fn.bindOnce = function(event, handler) {
        if (event === undefined || handler === undefined)
            return;
        var class_key = 'async_bindOnce_' + event;
        if (this.hasClass(class_key)) {
            return;
        }
        this.addClass(class_key);
 
        var events = this.data('events');

        if (events === undefined || events === null) {
            this.bind(event, handler);
        }
        else {
            if (events[event] === undefined) {
                this.bind(event, handler);
            }
            else {
                var isBound = false;
                $.each(events[event], function(i, eventHandler) {
                    if (eventHandler.toString() === handler.toString() || eventHandler == handler) {
                        isBound = true;
                        return false;
                    }
                });
 
                if (isBound === false) {
                    this.bind(event, handler);
                }
            }
        }
    };
})(jQuery);

(function($) {
    var timer = null, spinner = null;

    $.fn.spinner = function(state) {
        var self    = $(this);

        if (state === true) {
            timer = setTimeout(function () {
                timer = null;
                spinner = $loading.clone();
                self.after(spinner);
            }, 300);
        } else if (state == false) {
            if (timer) 
                clearTimeout(timer);
            else if (spinner)
                spinner.remove();
        } else {
            return spinner === null;
        }
    };
})(jQuery);
/*****/
 
var openDialog = null;
var editors    = new Array();

function _do_update(data, curpos) {
    for (var idx in data) {
        var block = data[idx];

        if (block.op == 'dialog_close') {
            if (openDialog) {
                openDialog.dialog('close');
                openDialog = null;
            }
        } else if (block.op == 'dialog') {
            var dialog = $('<div>'+block.body+'</div>');

            if (openDialog) 
                openDialog.dialog('close');

            openDialog = dialog;

            var options  = {
                title : block.title
            }
            if (block.dialogClass)
                options.dialogClass = block.dialogClass;
            if (block.modal)
                options.modal = block.modal;
            if (block.width)
                options.width = block.width;
            if (block.height)
                options.height = block.height;

            dialog.dialog(options)

            _bootstrap(dialog);
        } else if (block.op == 'focus') {
            $(block.selector).focus();
        } else if (block.op == 'redirect_url') {
            window.location.href = block.url;
        } else if (block.op == 'redirect') {
            if (block.dialog) {
                var dialog = $('<div></div>');
                dialog.load(block.url, function() {
                    openDialog = dialog;
                }).dialog();
            } else {
                $.ajax({
                    url : block.url,
                    type: 'GET',
                    dateType: 'json',
                    success: function(json) {
                        _do_update(json.actions, null);
                    },
                    error: function () {
                        showMessage('error', "An unexpected error has occured");
                    }
                });
            }
        } else if (block.op == 'track') {
            try {
                var pageTracker = _gat._getTracker("UA-9795826-1");
                pageTracker._trackPageview(block.url);
            } catch (e) { }
        } else if (block.op == 'history') {
            history.pushState({}, "", block.url);
        } else if (block.op == 'message') {
            if (block.type == 'error') {
                showMessage('error', block.html);
            } else {
                showMessage('success', block.html);
            }
        } else if (block.op == 'remove') {
            var sel = block.selector == 'this' ? curpos : $(block.selector);
            if (block.duration) {
                sel.fadeOut(block.duration);
            } else {
                sel.remove();
            }
        } else if (block.op == 'attr') {
            var sel = block.selector == 'this' ? curpos : $(block.selector);
            sel.attr(block.attr);
        } else {
            var sel = block.selector == 'this' ? curpos : $(block.selector);
            var html, h;
            var doboot = false;

            if (block.html != undefined) {
                if (block.html.indexOf('<') == -1) {
                    html = block.html;
                } else {
                    doboot = true;
                    html = $(block.html);
                }
            } else {
                html = block.text;
            }

            if (block.down_delay)
                html.hide();
            
            if (block.op == 'after') {
                h = sel.after(html);
            } else if (block.op == 'before') {
                h = sel.before(html);
            } else if (block.op == 'prepend') {
                h = sel.prepend(html);
            } else if (block.op == 'append') {
                h = sel.append(html);
            } else if (block.op == 'replace_with') {
                h = sel.replaceWith(html);
            } else if (block.op == 'replace') {
                h = sel.html(html);
            } else if (block.op == 'append') {
                h = sel.append(html);
            }

            if (block.down_delay)
                html.slideDown(block.down_delay);

            if (doboot) 
                _bootstrap(html);

            html = null;
        }
    }
}

function _bootstrap(html) {
    function findself(sel) {
        return html.is(sel) ? html.find(sel).add(html) : html.find(sel);
    }

    findself('form').each(function() {
        var form = $(this);
        var busy = false;

        form.find('textarea.rte').rte({
            no_source: true,
            fixed_tools: true,
            width: "100%",
            controls_rte: rte_simple_toolbar,
            controls_html: html_toolbar
        }, editors);

        form.find('.datepicker').datepicker({ inline: true });

        function handle_submit(event) {
            var self = $(this);
            var submits = [];

            var inDialog = ($(this).parents('.ui-dialog').length != 0);
            var inline   = ($(this).siblings('[rel="form"]').length != 0);

            form.unbind('submit', handle_submit);

            $(this).spinner(true);

            $('[type="submit"]', self).each(function () {
                submits.push([this, $(this).val(), $(this).attr('alt')]);
            });

            $(this).ajaxSubmit({
                dataType: 'json',
                success: function (response) {
                    if (response.actions) {
                        _do_update(response.actions, self);
                    }
                },
                complete: function(response) {
                    for (var x in submits) {
                        $(x[0]).val(x[1]);
                    }
                    submits = [];
                    $(this).spinner(false);
                    if (form[0].parentNode) {
                        form.submit(handle_submit);
                    } else {
                        form = null;
                    }
                }
            });

            for (var x in submits) {
                var alt = x[2];
                if (alt) $(x[0]).val(alt);
            }

            return false;
        }

        if ($(this).attr('rel') == 'async') {
            form.bindOnce('submit', handle_submit);
        }
    });

    /*
     * 
     */
    findself('[rel="toggle"]').each(function () {
        var href = $(this).attr('href');
        $(this).click(function() {
            $(this).toggleClass('toggle_open');
            if ($(href).css('display') == 'none') {
                $(href).show();
            } else {
                $(href).hide();
            }
            return false;
        });
    });

    findself('[rel="tooltip"]').each(function () {
        var val = $(this).attr('title');
        if (val) {
            $(this).tipTip({content: $(this).attr('title'),  edgeOffset: 10});
            $(this).attr('title', '');
        } else {
            $(this).tipTip({content: $(this).html(),  edgeOffset: 10});
        }
    });

    findself('[rel="close"]').each(function () {
        $(this).click(function () {
            if (openDialog) 
                openDialog.dialog('close');
            return false;
        })
    });

    findself('[rel="formtip"]').each(function () {
        var     sidebar = $($('.sidebar').get(0));
        var     dy = sidebar.offset().top;

        var     sel = $(this).get(0).getAttribute('for');
        var     pos = $(sel).offset();

        var     div = $('<div class="formtip"></div>').append($(this).html());
        $(this).remove();

        dy = 0;
        div.css({
            position: 'absolute',
        });

        sidebar.append(div);
        div.hide();

        (function (d) {
            function show_it() {
                var     pos = $(sel).offset();

                d.css('top', pos.top - dy - 8);

                d.show();
            }

            function hide_it() {
                d.hide();
            }

            if ($(sel).length != 0) {
                if ($(sel).get(0).tagName == 'IFRAME') {
                    $($(sel).contents().get(0)).bind('click', show_it);
                    $('body').click(hide_it);
                } else {
                    $(sel).focus(show_it);
                    $(sel).blur(hide_it);
                }
            }
        })(div);
    });

    findself('[rel="async"]').each(function() {
        if ($(this).attr('href')) {
            var self = this;
            var busy = false;

            var link = $(this).click(function() {
                var self = $(this);

                if (!busy) {
                    $(document).trigger('async_event');

                    var href = link.attr('href').split('#!')[1]

                    self.spinner(true);

                    $.ajax({
                        url : href,
                        type: 'GET',
                        dateType: 'json',
                        success: function(json) {
                            _do_update(json.actions, link);
                            if (window['async_event_complete']) {
                                window['async_event_complete']();
                            }
                        },
                        complete: function(response) {
                            busy = false;
                            $(this).spinner(false);
                        },
                        error: function () {
                            showMessage('error', "An unexpected error has occured");
                        }
                    });
                }

                return false;
            });
        }
    });

    findself('.closeable').each(function () {
        var span = $('<span class="close-icon">X</span>');
        var self = $(this);
        span.click(function () {
            if (self.attr('href')) {
                var href = self.attr('href').split('#!')[1]

                $.ajax({
                    url : href,
                    type: 'GET',
                    dateType: 'json',
                    success: function(json) {
                        _do_update(json.actions, self);
                    },
                    error: function () {
                        showMessage('error', "An unexpected error has occured");
                    }
                });
            } else {
                self.fadeOut(500);
                self = null;
            }
        });
        $(this).append(span);
    });

    findself('[rel="dialog"]').each(function() {
        var self = $(this);
        self.click(function () {
            next_page = self.attr('href').split('next=')[1]
            open(self.attr('href'),'asyncialog','height=600,width=800,toolbar=no,scrollbars=no');
            return false;
        });
    });

    findself('.action_add').each(function () {
        var id = $(this).attr('id');
        var href = $(this).attr('href');
        var lbl = $('[for="'+id+'"]');
        var html = $('<div class="adder"><a href="'+href+'" rel="async">Add</a></div>');

        lbl.after(html);

        _bootstrap(html);
    });

    findself('.default_label').each(function () {
        var self = this;
        var label = $('[for="'+ self.id + '"]');

        if ($(self).val() == '') {
            label.show();
        } else {
            label.hide();
        }

        $(self).focusin(function () {
            label.hide();
        });

        $(self).focusout(function () {
            if ($(self).val() == '') {
                label.show();
            }
        });

        $(self).change(function () {
            if ($(self).val() != '') {
                label.hide();
            } else {
                label.show();
            }
        });
    });

    findself('.default_text').each(function () {
        var self = $(this);
        var text = $(this).val();

        self.focusin(function () {
            if (self.hasClass('default_text')) {
                self.val('');
            }
            self.removeClass('default_text');
        });

        self.focusout(function () {
            if (self.val() == '') {
                self.val(text);
                self.addClass('default_text');
            }
        });

        self.closest('form').submit(function () {
            if (self.hasClass('default_text')) {
                self.val('');
            }
            self.removeClass('default_text');
        });
    });
};

$(document).ready(function() {
    $.ajaxSetup({
            'error' : function(e) {
                            showMessage('error', "An unexpected error has occured", e);
                            // alert('server communications failed');
                        }
    });

    _bootstrap($('body'));

    $(window).bind("popstate", function(e) {
        console.log("POP", document.location.pathname);
        $.ajax({
            url : document.location.pathname,
            type: 'GET',
            dateType: 'json',
            success: function(json) {
                _do_update(json.actions, null);
                /* TODO 
                if (window['async_event_complete']) {
                    window['async_event_complete']();
                }
                */
            },
            complete: function(response) {
            },
            error: function () {
                showMessage('error', "An unexpected error has occured");
            }
        });
    });
});
