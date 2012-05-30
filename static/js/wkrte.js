/*
 * WKRTE - jQuery Plugin, version 0.1 
 * http://code.google.com/p/wkrte/
 * License: MIT license
 */


/***
 * START TOOLBAR
 */
var rte_tag		= '-rte-tmp-tag-';

var	rte_simple_toolbar = {
	undo            : {command: 'undo'},
	redo            : {command: 'redo'},
	s2              : {separator: true},
	bold            : {command: 'bold', tags:['b', 'strong']},
	italic          : {command: 'italic', tags:['i', 'em']},
	underline       : {command: 'underline', tags: ['u']},
	s4              : {separator : true },
	orderedList     : {command: 'insertorderedlist', tags: ['ol'] },
	unorderedList   : {command: 'insertunorderedlist', tags: ['ul'] },
	s5              : {separator : true},
	indent          : {command: 'indent'},
	outdent         : {command: 'outdent'},	
	s6              : {separator : true},
	link            : {exec: lwrte_link, tags: ['a'] },
	unlink          : {command: 'unlink'}
};

var	rte_toolbar = {
	s1              : {separator : true},
	undo            : {command: 'undo'},
	redo            : {command: 'redo'},
	s2              : {separator: true},
	bold            : {command: 'bold', tags:['b', 'strong']},
	italic          : {command: 'italic', tags:['i', 'em']},
/*
	strikeThrough   : {command: 'strikethrough', tags: ['s', 'strike'] },
*/
	underline       : {command: 'underline', tags: ['u']},
	s3              : {separator: true},
	p               : {command : 'formatBlock', args : ['p'], tags : ['p']},	
	h1              : {command : 'formatBlock', args : ['h1'], tags : ['h1']},	 
	h2              : {command : 'formatBlock', args : ['h2'], tags : ['h2']},	 
	h3              : {command : 'formatBlock', args : ['h3'], tags : ['h3']},		
/*Headings h4, h5, h6 disabled by default
	h4              : {command : 'formatBlock', args : ['h4'], tags : ['h4']},	 
	h5              : {command : 'formatBlock', args : ['h5'], tags : ['h5']},	 
	h6              : {command : 'formatBlock', args : ['h6'], tags : ['h6']}, 
*/ 
	s4              : {separator : true },
	orderedList     : {command: 'insertorderedlist', tags: ['ol'] },
	unorderedList   : {command: 'insertunorderedlist', tags: ['ul'] },
	s5              : {separator : true },
	justifyLeft     : {command: 'justifyleft'},
	justifyCenter   : {command: 'justifycenter'},
	justifyRight    : {command: 'justifyright'},
/*
	justifyFull     : {command: 'justifyfull'},
*/
	s6              : {separator : true},
	indent          : {command: 'indent'},
	outdent         : {command: 'outdent'},	
/*
	s7              : {separator : true},
	subscript       : {command: 'subscript', tags: ['sub']},
	superscript     : {command: 'superscript', tags: ['sup']},
*/
	s8              : {separator: true },
	color           : {exec: lwrte_color},
	image           : {exec: lwrte_image, tags: ['img'] },
	link            : {exec: lwrte_link, tags: ['a'] },
	unlink          : {command: 'unlink'},
	s9              : {separator : true },
	removeFormat    : {exec: lwrte_unformat},
	clear           : {exec: lwrte_clear}
};

var html_toolbar = {
	s1              : {separator: true},
	clear           : {exec: lwrte_clear}
};

/* tag compare callbacks */
function lwrte_block_compare(node, tag) {
	tag = tag.replace(/<([^>]*)>/, '$1');
	return (tag.toLowerCase() == node.nodeName.toLowerCase());
};

/* init callbacks */
function lwrte_style_init(rte) {
	var self = this;
	self.select = '<select><option value="">- no css -</option></select>';

	// load CSS info. javascript only issue is not working correctly, that's why ajax-php :(
	if(rte.css.length) {	
		$.ajax({
			url: "styles.php", 
			type: "POST",
			data: { css: rte.css[rte.css.length - 1] }, 
			async: false,
			success: function(data) {
				var list = data.split(',');
				var select = "";

				for(var name in list)
					select += '<option value="' + list[name] + '">' + list[name] + '</option>';
	
				self.select = '<select><option value="">- css -</option>' + select + '</select>';
			}});
	}
};

/*
 * Panel: unformat html
 */
function lwrte_unformat() {
	this.editor_cmd('removeFormat');
	this.editor_cmd('unlink');
};


/*
 * Panel: clear textarea (will delete all content)
 */
function lwrte_clear() {
	if(confirm('Clear Document?')) 
		this.set_content('');
};

/*
 * Panel: Set color for text
 */
function lwrte_color(){
	var self = this;
	var panel = self.create_panel('<span class="panel-title-color">Set color for text</span>', 355);
	var mouse_down = false;
	panel.append('\
<div class="rte-panel-wrap">\
<div class="colorpicker"><div class="rgb" id="rgb"></div></div>\
<div class="colorpicker"><div class="gray" id="gray"></div></div>\
<div class="palette" id="palette"></div>\
<div class="clear"></div>\
<div class="submit">\
<a class="button" id="ok"><span>Ok</span></a><a class="button" id="cancel"><span>Cancel</span></a>\
<div class="colorPreview">\
	<div class="preview" id="preview"></div>\
	<div class="color" id="color"></div>\
</div>\
</div>\
<div class="clear"></div>\
</div>'
).show();

	var preview = $('#preview', panel);
	var color = $("#color", panel);
	var palette = $("#palette", panel);
	var colors = [
		'#660000', '#990000', '#cc0000', '#ff0000', '#333333',
		'#006600', '#009900', '#00cc00', '#00ff00', '#666666',
		'#000066', '#000099', '#0000cc', '#0000ff', '#999999',
		'#909000', '#900090', '#009090', '#ffffff', '#cccccc',
		'#ffff00', '#ff00ff', '#00ffff', '#000000', '#eeeeee'
	];
			
	for(var i = 0; i < colors.length; i++)
		$("<div></div>").addClass("item").css('background', colors[i]).appendTo(palette);
			
	var height = $('#rgb').height();
	var part_width = $('#rgb').width() / 6;

	$('#rgb,#gray,#palette', panel)
		.mousedown( function(e) {mouse_down = true; return false; } )
		.mouseup( function(e) {mouse_down = false; return false; } )
		.mouseout( function(e) {mouse_over = false; return false; } )
		.mouseover( function(e) {mouse_over = true; return false; } );

	$('#rgb').mousemove( function(e) { if(mouse_down && mouse_over) compute_color(this, true, false, false, e); return false;} );
	$('#gray').mousemove( function(e) { if(mouse_down && mouse_over) compute_color(this, false, true, false, e); return false;} );
	$('#palette').mousemove( function(e) { if(mouse_down && mouse_over) compute_color(this, false, false, true, e); return false;} );
	$('#rgb').click( function(e) { compute_color(this, true, false, false, e); return false;} );
	$('#gray').click( function(e) { compute_color(this, false, true, false, e); return false;} );
	$('#palette').click( function(e) { compute_color(this, false, false, true, e); return false;} );

	$('#cancel', panel).click( function() { panel.remove(); return false; } );
	$('#ok', panel).click( 
		function() {
			var value = color.html();

			if(value.length > 0 && value.charAt(0) =='#') {
				if(self.iframe_doc.selection) //IE fix for lost focus
					self.range.select();

				self.editor_cmd('foreColor', value);
			}
					
			panel.remove(); 
			return false;
		}
	);

	function to_hex(n) {
		var s = "0123456789abcdef";
		return s.charAt(Math.floor(n / 16)) + s.charAt(n % 16);
	}			

	function get_abs_pos(element) {
		var r = { x: element.offsetLeft, y: element.offsetTop };

		if (element.offsetParent) {
			var tmp = get_abs_pos(element.offsetParent);
			r.x += tmp.x;
			r.y += tmp.y;
		}

		return r;
	};
			
	function get_xy(obj, event) {
		var x, y;
		event = event || window.event;
		var el = event.target || event.srcElement;

		// use absolute coordinates
		var pos = get_abs_pos(obj);

		// subtract distance to middle
		x = event.pageX  - pos.x;
		y = event.pageY - pos.y;

		return { x: x, y: y };
	}
			
	function compute_color(obj, is_rgb, is_gray, is_palette, e) {
		var r, g, b, c;

		var mouse = get_xy(obj, e);
		var x = mouse.x;
		var y = mouse.y;

		if(is_rgb) {
			r = (x >= 0)*(x < part_width)*255 + (x >= part_width)*(x < 2*part_width)*(2*255 - x * 255 / part_width) + (x >= 4*part_width)*(x < 5*part_width)*(-4*255 + x * 255 / part_width) + (x >= 5*part_width)*(x < 6*part_width)*255;
			g = (x >= 0)*(x < part_width)*(x * 255 / part_width) + (x >= part_width)*(x < 3*part_width)*255	+ (x >= 3*part_width)*(x < 4*part_width)*(4*255 - x * 255 / part_width);
			b = (x >= 2*part_width)*(x < 3*part_width)*(-2*255 + x * 255 / part_width) + (x >= 3*part_width)*(x < 5*part_width)*255 + (x >= 5*part_width)*(x < 6*part_width)*(6*255 - x * 255 / part_width);

			var k = (height - y) / height;

			r = 128 + (r - 128) * k;
			g = 128 + (g - 128) * k;
			b = 128 + (b - 128) * k;
		} else if (is_gray) {
			r = g = b = (height - y) * 1.7;
		} else if(is_palette) {
			x = Math.floor(x / 10);
			y = Math.floor(y / 10);
			c = colors[x + y * 5];
		}

		if(!is_palette)
			c = '#' + to_hex(r) + to_hex(g) + to_hex(b);

		preview.css('background', c);
		color.html(c);
	}
};

/*
 * Panel: insert image
 */
function lwrte_image() {
	var self = this;
	var panel = self.create_panel('<span class="panel-title-image">Insert image</span>', 350);
	panel.append('\
<div class="rte-panel-wrap">\
<p><label>Image URL:</label><input type="text" id="url" size="50" value=""></p>\
<div class="clear"></div>\
<p class="submit"><a class="button" id="ok"><span>Ok</span></a><a class="button" id="cancel"><span>Cancel</span></a></p>\
<div class="clear"></div>\
</div>'
).show();

	var url = $('#url', panel);
	var upload = $('#file', panel).upload( {
		autoSubmit: false,
		action: 'uploader.php',
		onSelect: function() {
			var file = this.filename();
			var ext = (/[.]/.exec(file)) ? /[^.]+$/.exec(file.toLowerCase()) : '';
			if(!(ext && /^(jpg|png|jpeg|gif)$/.test(ext))){
				alert('Invalid file extension');
				return;
			}

			this.submit();
		},
		onComplete: function(response) { 
			if(response.length <= 0)
				return;

			response	= eval("(" + response + ")");
			if(response.error && response.error.length > 0)
				alert(response.error);
			else
				url.val((response.file && response.file.length > 0) ? response.file : '');
		}
	});

	$('#view', panel).click( function() {
			(url.val().length >0 ) ? window.open(url.val()) : alert("Enter URL of image to view");
			return false;
		}
	);
			
	$('#cancel', panel).click( function() { panel.remove(); return false;} );
	$('#ok', panel).click( 
		function() {
			var file = url.val();	
			(url.val().length >0 ) ? window.open(url.val()) : alert("Enter URL of image to view");
			return false;	
			
			self.editor_cmd('insertImage', file);
			panel.remove(); 
			return false;
		}
	)
};

/*
 * Panel: Insert link
 */
function lwrte_link() {
    var self = this;

    $('\
<div class="form_style">\
<p><label for="wkre_dialog_url">Link URL:</label><input type="text" id="wkre_dialog_url" size="50" value=""></p>\
</div>\
').dialog({
    buttons: {
        'Ok' : function() {
            var url   = $(this).find('#wkre_dialog_url').val();
            var title = $(this).find('#wkre_dialog_text').val();

            $(this).dialog('close');
            $(this).remove();

			if (url.length <= 0)
				return false;

			self.editor_cmd('unlink');

			// we wanna well-formed linkage (<p>,<h1> and other block types can't be inside of link due to WC3)
            var h = self.get_selected_html();

            if (h.length == 0)
                h = url;

			self.editor_cmd('createLink', rte_tag);

			//var tmp = $('<span></span>').append(self.get_selected_html());
			// $('a[href*="' + rte_tag + '"]', tmp).attr('href', url);
				
            var tmp = $('<a href="#"></a>').attr('href', url).append(h);

			self.selection_replace_with($('<span></span>').append(tmp).html());
        },
        'Cancel' : function() {
            $(this).dialog('close');
            $(this).remove();
        }
    }
});
};

function xlwrte_link() {
	var self = this;
	var panel = self.create_panel('<span class="panel-title-link">Insert Link</span>', 350);

	panel.append('\
<div class="rte-panel-wrap">\
<p><label>Link URL:</label><input type="text" id="url" size="50" value=""></p>\
<div class="clear"></div>\
<p><label>Text to display:</label><input type="text" id="title" size="50" value=""></p>\
<div class="clear"></div>\
<p><label>Target</label><select id="target"><option value="">default</option><option value="_blank">Open in a new tab</option></select></p>\
<div class="clear"></div>\
<p class="submit"><a class="button" id="ok"><span>Ok</span></a><a class="button" id="cancel"><span>Cancel</span></a></p>\
<div class="clear"></div>\
</div>'
).show();

	$('#cancel', panel).click( function() { panel.remove(); return false; } );

	var url = $('#url', panel);

	$('#ok', panel).click( 
		function() {
			var url = $('#url', panel).val();
			var target = $('#target', panel).val();
			var title = $('#title', panel).val();

			if(self.get_selected_text().length <= 0) {
				alert('Select the text you wish to link!');
				return false;
			}

			panel.remove(); 

			if(url.length <= 0)
				return false;

			self.editor_cmd('unlink');

			// we wanna well-formed linkage (<p>,<h1> and other block types can't be inside of link due to WC3)
			self.editor_cmd('createLink', rte_tag);
			var tmp = $('<span></span>').append(self.get_selected_html());

			if(target.length > 0)
				$('a[href*="' + rte_tag + '"]', tmp).attr('target', target);

			if(title.length > 0)
				$('a[href*="' + rte_tag + '"]', tmp).attr('title', title);

			$('a[href*="' + rte_tag + '"]', tmp).attr('href', url);
				
			self.selection_replace_with(tmp.html());
			return false;
		}
	)
};

/***
 * Create iFrame
 * Code below will format the textarea
 */
jQuery.fn.rte = function(options, editors) {
	if(!editors || editors.constructor != Array) {
		editors = new Array();
    }
		
	$(this).each(function(i) {
		var id = (this.id) ? this.id : editors.length;
		editors[id] = new lwRTE (this, options || {});
	});

	return editors;
};

var lwRTE_resizer = function(textarea) {
	this.drag = false;
	this.rte_zone = $(textarea).parents('.rte-zone');
};

lwRTE_resizer.mousedown = function(resizer, e) {
	resizer.drag = true;
	resizer.event = (typeof(e) == "undefined") ? window.event : e;
	resizer.rte_obj = $(".rte-resizer", resizer.rte_zone).prev().eq(0);
	$('body', document).css('cursor', 'se-resize');
	return false;
};

lwRTE_resizer.mouseup = function(resizer, e) {
	resizer.drag = false;
	$('body', document).css('cursor', 'auto');
	return false;
};

lwRTE_resizer.mousemove = function(resizer, e) {
	if(resizer.drag) {
		e = (typeof(e) == "undefined") ? window.event : e;
		var w = Math.max(1, resizer.rte_zone.width() + e.screenX - resizer.event.screenX);
		var h = Math.max(1, resizer.rte_obj.height() + e.screenY - resizer.event.screenY);
		resizer.rte_zone.width(w);
		resizer.rte_obj.height(h);
		resizer.event = e;
	}
	return false;
};

var lwRTE = function (textarea, options) {
	this.css		= [];
	this.css_class	= options.frame_class || '';
	this.base_url	= options.base_url || '';
	this.width		= options.width || $(textarea).width() || '100%';
	this.height		= options.height || $(textarea).height() || 350;
    this.fixed_toolbar= options.fixed_tools || false;
	this.iframe		= null;
	this.iframe_doc	= null;
	this.textarea	= null;
	this.event		= null;
	this.range		= null;
	this.toolbars	= {rte: '', html : ''};

    if (options.no_source) {
        this.controls	= { rte: {}, html: {}};
    } else {
        this.controls	= {rte: {disable: {hint: 'Source editor'}}, html: {enable: {hint: 'Visual editor'}}};
    }

	$.extend(this.controls.rte, options.controls_rte || {});
	$.extend(this.controls.html, options.controls_html || {});
	$.extend(this.css, options.css || {});

	if(document.designMode || document.contentEditable) {		
		$(textarea).wrap($('<div></div>').addClass('rte-zone').width(this.width));		
		$('<div class="rte-resizer"><a href="#"></a></div>').insertAfter(textarea);

        if (this.fixed_toolbar)
            $('<div class="rte-tools"><a href="#"></a></div>').insertBefore(textarea);

		var resizer = new lwRTE_resizer(textarea);
		
		$(".rte-resizer a", $(textarea).parents('.rte-zone')).mousedown(function(e) {
			$(document).mousemove(function(e) {
				return lwRTE_resizer.mousemove(resizer, e);
			});

			$(document).mouseup(function(e) {
				return lwRTE_resizer.mouseup(resizer, e)
			});

			return lwRTE_resizer.mousedown(resizer, e);
		});

		this.textarea	= textarea;
		this.enable_design_mode();
	}
};

lwRTE.prototype.editor_cmd = function(command, args) {
	this.iframe.contentWindow.focus();
	try {
		this.iframe_doc.execCommand(command, false, args);
	} catch(e) {
	}
	this.iframe.contentWindow.focus();
};

lwRTE.prototype.get_toolbar = function() {
	var editor = (this.iframe) ? $(this.iframe) : $(this.textarea);
	return (editor.prev().hasClass('rte-toolbar')) ? editor.prev() : null;
};

lwRTE.prototype.activate_toolbar = function(editor, tb) {
	var old_tb = this.get_toolbar();

	if(old_tb)
		old_tb.remove();

	$(editor).before($(tb).clone(true));
};
	
lwRTE.prototype.enable_design_mode = function(){
	var self = this;
	
	// need to be created this way
	self.iframe = document.createElement("iframe");
	self.iframe.frameBorder = 0;
	self.iframe.frameMargin = 0;
	self.iframe.framePadding = 0;
	self.iframe.width = '100%';
	self.iframe.height = self.height || '100%';
	self.iframe.src = "javascript:void(0);";
	
	if ($(self.textarea).attr('class')) 
		self.iframe.className = $(self.textarea).attr('class');
	
	if ($(self.textarea).attr('id')) 
		self.iframe.id = $(self.textarea).attr('id');
	
	if ($(self.textarea).attr('name')) 
		self.iframe.title = $(self.textarea).attr('name');
	
	var content = $(self.textarea).val();
	
	$(self.textarea).hide().after(self.iframe).remove();
	self.textarea = null;
	
	var css = '';
	
	for (var i in self.css) 
		css += "<link type='text/css' rel='stylesheet' href='" + self.css[i] + "' />";
	
	var base = (self.base_url) ? "<base href='" + self.base_url + "' />" : '';
	var style = (self.css_class) ? "class='" + self.css_class + "'" : '';
	
	// Mozilla need this to display caret
	/*if($.trim(content) == '')
	 content	= '<br>';*/
	var doc = "<html><head>" + base + css + "</head><body class='rte-body' " + style + " style='padding:5px'>" + content + "</body></html>";
	
	self.iframe_doc = self.iframe.contentWindow.document;
	
	try {
		self.iframe_doc.designMode = 'on';
	} 
	catch (e) {
		// Will fail on Gecko if the editor is placed in an hidden container element
		// The design mode will be set ones the editor is focused
		$(self.iframe_doc).focus(function(){
			self.iframe_doc.designMode();
		});
	}
	
	self.iframe_doc.open();
	self.iframe_doc.write(doc);
	self.iframe_doc.close();
	
	if (!self.toolbars.rte) 
		self.toolbars.rte = self.create_toolbar(self.controls.rte);
	
	self.activate_toolbar(self.iframe, self.toolbars.rte);
	
	$(self.iframe).parents('form').submit(function(){
		self.disable_design_mode(true);
	});
	
	$(self.iframe_doc).mouseup(function(event){
		if (self.iframe_doc.selection) 
			self.range = self.iframe_doc.selection.createRange(); //store to restore later(IE fix)
		self.set_selected_controls((event.target) ? event.target : event.srcElement, self.controls.rte);
	});
	
	$(self.iframe_doc).blur(function(event){
		if (self.iframe_doc.selection) 
			self.range = self.iframe_doc.selection.createRange(); // same fix for IE as above
	});
	
	$(self.iframe_doc).keyup(function(event){
		self.set_selected_controls(self.get_selected_element(), self.controls.rte);
	});
	
	// Mozilla CSS styling off
	if (!$.browser.msie) 
		self.editor_cmd('styleWithCSS', false);
	
	
	// FadeIn/FadeOut Toolbar
	//returns the document of the iframe: http://brandonaaron.net/blog/2009/05/14/jquery-edge-better-support-for-other-windows-and-documents 
	var iframeClickEvents = $('iframe').contents().get(0);
	
    if (! self.fixed_toolbar) {
        $(iframeClickEvents).bind('click', function(event){
            $(".rte-toolbar").fadeIn();
            event.stopPropagation();
        });
	
        $("body").addClass('jrte-body');
        $("body.jrte-body").click(function(event){ // On mouseenter, show toolbar
            $(".rte-toolbar").fadeOut();
            event.stopPropagation();
        });
    }
};

    
lwRTE.prototype.disable_design_mode = function(submit) {
	var self = this;

	self.textarea = (submit) ? $('<input type="hidden" />').get(0) : $('<textarea></textarea>').width('100%').height(self.height).get(0);

	if(self.iframe.className)
		self.textarea.className = self.iframe.className;

	if(self.iframe.id)
		self.textarea.id = self.iframe.id;
		
	if(self.iframe.title)
		self.textarea.name = self.iframe.title;
	
	$(self.textarea).val($('body', self.iframe_doc).html());
	$(self.iframe).before(self.textarea);

	if(!self.toolbars.html)
		self.toolbars.html	= self.create_toolbar(self.controls.html);

	if(submit != true) {
		$(self.iframe_doc).remove(); //fix 'permission denied' bug in IE7 (jquery cache)
		$(self.iframe).remove();
		self.iframe = self.iframe_doc = null;
		self.activate_toolbar(self.textarea, self.toolbars.html);
	}
};
    
lwRTE.prototype.toolbar_click = function(obj, control) {
	var fn = control.exec;
	var args = control.args || [];
	var is_select = (obj.tagName.toUpperCase() == 'SELECT');
	
	$('.rte-panel', this.get_toolbar()).remove();

	if(fn) {
		if(is_select)
			args.push(obj);

		try {
			fn.apply(this, args);
		} catch(e) {

		}
	} else if(this.iframe && control.command) {
		if(is_select) {
			args = obj.options[obj.selectedIndex].value;

			if(args.length <= 0)
				return;
		}

		this.editor_cmd(control.command, args);
	}
};

/***
 * CREATE TOOLBAR
 */
lwRTE.prototype.create_toolbar = function(controls) {
	var self = this;

    var tb;
    if (self.fixed_toolbar) {
        tb = $("<div></div>").addClass('rte-toolbar').addClass('fixed').append($("<div></div>").addClass('rte-toolbar-wrap').append($("<ul></ul>")));
    } else {
        tb = $("<div></div>").addClass('rte-toolbar').addClass('floating').append($("<div></div>").addClass('rte-toolbar-wrap').append($("<ul></ul>")).append($("<div></div>").addClass('rte-toolbar-arrow'))).hide();
    }
	var obj, li;	
	
	for (var key in controls){
		if(controls[key].separator) {
			li = $("<li></li>").addClass('separator');
		} else {
			if(controls[key].init) {
				try {
					controls[key].init.apply(controls[key], [this]);
				} catch(e) {
				}
			}
			
			if(controls[key].select) {
				obj = $(controls[key].select)
					.change( function(e) {
						self.event = e;
						self.toolbar_click(this, controls[this.className]); 
						return false;
					});
			} else {
				obj = $("<a href='#'></a>")
					.attr('title', (controls[key].hint) ? controls[key].hint : key)
					.attr('rel', key)
					.click( function(e) {
						self.event = e;
						self.toolbar_click(this, controls[this.rel]); 
						return false;
					})
					.mouseover( function(e) {						
						$(this).parent().addClass("rte-hover");
						return false;
					})
					.mouseover( function(e) {						
						$(this).parent().addClass("rte-hover");
						return false;
					}).bind('mouseleave',function(){ // On mouseleave
						$(this).parent().removeClass("rte-hover");
					})
			}

			li = $("<li></li>").append(obj.addClass(key));
			
		}

		$("ul",tb).append(li);
	}

	$(tb).click(function() {
		$(".rte-toolbar").show();
		return false; 
	});

	$('.enable', tb).click(function() {
		self.enable_design_mode();
		$(".rte-toolbar").show();
		return false; 
	});

	$('.disable', tb).click(function() {
		self.disable_design_mode();
		$(".rte-toolbar").show().css({
			'width': '80px'
		});	
		$('textarea').click(function(event){
			$(".rte-toolbar").fadeIn();
			event.stopPropagation();
		});
		return false; 
	});	

	return tb.get(0);
	
};

/***
 * CREATE PANELS
 */
lwRTE.prototype.create_panel = function(title, width) {
	var self = this;
	var tb = self.get_toolbar();

	if(!tb)
		return false;

	$('.rte-panel', tb).remove();
	var drag, event;
	var left = self.event.pageX;
	var top = self.event.pageY;
	
	var panel	= $('<div></div>').hide().addClass('rte-panel').css({left: left, top: top}); //THIS IS NOT WORKING AS EXPECTED!!! NEED IMMEDIATE ATTENTION FROM DEVELOPERS
	
	$('<div></div>')	
		.addClass('rte-panel-title')
		.append($("<div></div>").addClass('rte-panel-title-wrap')
		.append($("<span></span>")
		.html(title))
		.append($("<a class='close' href='#'>&nbsp;</a>")
		.click( function() { panel.remove(); return false; }))
		.mousedown( function() { drag = true; return false; })
		.mouseup( function() { drag = false; return false; })
		.mousemove( 
			function(e) {
				if(drag && event) {
					left -= event.pageX - e.pageX;
					top -=  event.pageY - e.pageY;
					panel.css( {left: left, top: top} ); 
				}

				event = e;
				return false;
			} 
		))
		.appendTo(panel);

	if(width)
		panel.width(width);

	tb.append(panel);
	return panel;
};

lwRTE.prototype.get_content = function() {
	return (this.iframe) ? $('body', this.iframe_doc).html() : $(this.textarea).val();
};

lwRTE.prototype.set_content = function(content) {
	(this.iframe) ? $('body', this.iframe_doc).html(content) : $(this.textarea).val(content);
};

lwRTE.prototype.set_selected_controls = function(node, controls) {
	var toolbar = this.get_toolbar();

	if(!toolbar)
		return false;
		
	var key, i_node, obj, control, tag, i, value, li;

	try {
		for (key in controls) {
			control = controls[key];
			obj = $('.' + key, toolbar);

			obj.parents('li').removeClass('active');

			if(!control.tags)
				continue;

			i_node = node;
			do {
				if(i_node.nodeType != 1)
					continue;

				tag	= i_node.nodeName.toLowerCase();
				if($.inArray(tag, control.tags) < 0 )
					continue;

				if(control.select) {
					obj = obj.get(0);
					if(obj.tagName.toUpperCase() == 'SELECT') {
						obj.selectedIndex = 0;

						for(i = 0; i < obj.options.length; i++) {
							value = obj.options[i].value;
							if(value && ((control.tag_cmp && control.tag_cmp(i_node, value)) || tag == value)) {
								obj.selectedIndex = i;
								break;
							}
						}
					}
				} else
					obj.parents('li').addClass('active');
			}  while(i_node = i_node.parentNode)
		}
	} catch(e) {
	}
	
	return true;
};

lwRTE.prototype.get_selected_element = function () {
	var node, selection, range;
	var iframe_win	= this.iframe.contentWindow;
	
	if (iframe_win.getSelection) {
		try {
			selection = iframe_win.getSelection();
			range = selection.getRangeAt(0);
			node = range.commonAncestorContainer;
		} catch(e){
			return false;
		}
	} else {
		try {
			selection = iframe_win.document.selection;
			range = selection.createRange();
			node = range.parentElement();
		} catch (e) {
			return false;
		}
	}

	return node;
};

lwRTE.prototype.get_selection_range = function() {
	var rng	= null;
	var iframe_window = this.iframe.contentWindow;
	this.iframe.focus();
	
	if(iframe_window.getSelection) {
		rng = iframe_window.getSelection().getRangeAt(0);
		if($.browser.opera) { //v9.63 tested only
			var s = rng.startContainer;
			if(s.nodeType === Node.TEXT_NODE)
				rng.setStartBefore(s.parentNode);
		}
	} else {
		this.range.select(); //Restore selection, if IE lost focus.
		rng = this.iframe_doc.selection.createRange();
	}

	return rng;
};

lwRTE.prototype.get_selected_text = function() {
	var iframe_win = this.iframe.contentWindow;

	if(iframe_win.getSelection)	
		return iframe_win.getSelection().toString();

	this.range.select(); //Restore selection, if IE lost focus.
	return iframe_win.document.selection.createRange().text;
};

lwRTE.prototype.get_selected_html = function() {
	var html = null;
	var iframe_window = this.iframe.contentWindow;
	var rng	= this.get_selection_range();

	if(rng) {
		if(iframe_window.getSelection) {
			var e = document.createElement('div');
			e.appendChild(rng.cloneContents());
			html = e.innerHTML;		
		} else {
			html = rng.htmlText;
		}
	}

	return html;
};
	
lwRTE.prototype.selection_replace_with = function(html) {
	var rng	= this.get_selection_range();
	var iframe_window = this.iframe.contentWindow;

	if(!rng)
		return;
	
	this.editor_cmd('removeFormat'); // we must remove formating or we will get empty format tags!

	if(iframe_window.getSelection) {
		rng.deleteContents();
		rng.insertNode(rng.createContextualFragment(html));
		this.editor_cmd('delete');
	} else {
		this.editor_cmd('delete');
		rng.pasteHTML(html);
	}
};

lwRTE.prototype.val = function() {
    return $('body', this.iframe_doc).html();
}
