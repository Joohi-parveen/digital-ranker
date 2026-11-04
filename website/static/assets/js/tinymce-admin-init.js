document.addEventListener('DOMContentLoaded', function() {
    if (typeof tinymce === 'undefined') return;

    tinymce.init({
        selector: '#id_content',
        height: 500,
        min_height: 420,
        menubar: false,
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount', 'directionality'
        ],
        toolbar: [
            'blocks | bold italic underline strikethrough | link image table | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | blockquote hr | removeformat | code fullscreen preview | undo redo'
        ],
        block_formats: 'Paragraph=p; Heading 1=h1; Heading 2=h2; Heading 3=h3; Heading 4=h4; Heading 5=h5; Heading 6=h6; Blockquote=blockquote; Preformatted=pre',
        branding: false,
        promotion: false,
        elementpath: true,
        resize: true,
        convert_urls: false,
        relative_urls: false,
        remove_script_host: false,
        default_link_target: '_blank',
        link_assume_external_targets: true,
        image_title: true,
        image_caption: true,
        image_advtab: true,
        table_responsive_width: true,
        content_style: `
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
                font-size: 15px; 
                line-height: 1.8; 
                color: #334155; 
                padding: 16px 20px;
            }
            h1, h2, h3, h4, h5, h6 { color: #1e293b; font-weight: 700; margin-top: 1.4em; margin-bottom: 0.6em; line-height: 1.3; }
            h1 { font-size: 2.2rem; }
            h2 { font-size: 1.8rem; }
            h3 { font-size: 1.5rem; }
            h4 { font-size: 1.25rem; }
            h5 { font-size: 1.1rem; }
            h6 { font-size: 1rem; }
            p { margin-bottom: 1.2em; }
            a { color: #6B2E88; text-decoration: underline; }
            blockquote { border-left: 4px solid #6B2E88; margin: 1.5em 0; padding: 12px 20px; background: #f8fafc; font-style: italic; color: #475569; border-radius: 0 8px 8px 0; }
            table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
            table th, table td { border: 1px solid #e2e8f0; padding: 10px 14px; }
            table th { background: #f1f5f9; font-weight: 600; }
            img { max-width: 100%; height: auto; border-radius: 8px; }
            hr { border: none; border-top: 1px solid #e2e8f0; margin: 2em 0; }
            ul, ol { padding-left: 24px; margin-bottom: 1.2em; }
            li { margin-bottom: 0.4em; }
            code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #d63384; }
            pre { background: #1e293b; color: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto; }
        `,
        setup: function(editor) {
            editor.on('change keyup input paste NodeChange', function() {
                editor.save();
            });
        }
    });
});
