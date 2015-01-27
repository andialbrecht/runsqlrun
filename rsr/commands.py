commands = {
    'app': {
        'label': 'Application',
        'actions': {
            'neweditor': {
                'label': 'New SQL editor',
                'description': 'Open new SQL editor',
                'icon': 'document-new-symbolic',
                'shortcut': '<Control>N',
                'callback': 'win.docview.add_worksheet'
            }
        }
    },
    'editor': {
        'label': 'SQL Editor',
        'actions': {
            'run': {
                'label': 'Run SQL statement',
                'description': 'Run SQL statement at cursor',
                'icon': 'media-playback-start-symbolic',
                'shortcut': '<Control>Return',
                'callback': 'run_query'
            }
        }
    }
}
