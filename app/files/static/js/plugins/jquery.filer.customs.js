let filer_options = {
  templates: {
    box: '<ul class="jFiler-items-list jFiler-items-grid"></ul>',
    item: '<li class="jFiler-item">\
						<div class="jFiler-item-container">\
							<div class="jFiler-item-inner">\
								<div class="jFiler-item-thumb">\
									<div class="jFiler-item-status"></div>\
									<div class="jFiler-item-thumb-overlay">\
										<div class="jFiler-item-info">\
											<div style="display:table-cell;vertical-align: middle;">\
												<span class="jFiler-item-title"><b title="{{fi-name}}">{{fi-name}}</b></span>\
												<span class="jFiler-item-others">{{fi-size2}}</span>\
											</div>\
										</div>\
									</div>\
									{{fi-image}}\
								</div>\
								<div class="jFiler-item-assets jFiler-row">\
									<ul class="list-inline pull-left">\
										<li>{{fi-progressBar}}</li>\
									</ul>\
								</div>\
							</div>\
						</div>\
					</li>',
    itemAppend: '<li class="jFiler-item">\
							<div class="jFiler-item-container">\
								<div class="jFiler-item-inner">\
									<div class="jFiler-item-thumb">\
										<div class="jFiler-item-status"></div>\
										<div class="jFiler-item-thumb-overlay">\
											<div class="jFiler-item-info">\
												<div style="display:table-cell;vertical-align: middle;">\
													<span class="jFiler-item-title"><b title="{{fi-name}}">{{fi-name}}</b></span>\
													<span class="jFiler-item-others">{{fi-size2}}</span>\
												</div>\
											</div>\
										</div>\
										{{fi-image}}\
									</div>\
									<div class="jFiler-item-assets jFiler-row">\
										<ul class="list-inline pull-left">\
											<li><span class="jFiler-item-others">{{fi-icon}}</span></li>\
										</ul>\
									</div>\
								</div>\
							</div>\
						</li>',
    progressBar: '<div class="bar"></div>',
    itemAppendToEnd: false,
    canvasImage: true,
    removeConfirmation: false,
    _selectors: {
      list: '.jFiler-items-list',
      item: '.jFiler-item',
      progressBar: '.bar',
      remove: null,
    }
  },
  captions: {
    button: "Choose Files",
    feedback: "Choose files To Upload",
    feedback2: "files were chosen",
    drop: "Drop file here to Upload",
    removeConfirmation: "Are you sure you want to remove this file?",
    errors: {
      filesLimit: "Only {{fi-limit}} files are allowed to be uploaded.",
      filesType: "Only Images are allowed to be uploaded.",
      filesSize: "{{fi-name}} is too large! Please upload file up to {{fi-maxSize}} MB.",
      filesSizeAll: "Files you've choosed are too large! Please upload files up to {{fi-maxSize}} MB."
    }
  },
};