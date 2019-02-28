const path = require('path');
const fs = require('fs-extra');
const _ = require('underscore');

const TARGETS = [
    './ui/static/vendors/js',
    './ui/static/vendors/css',
    './ui/static/vendors/css/img',
    './ui/static/vendors/webfonts'
];

const ASSETS = {
    '@fortawesome/fontawesome-free/js/all.min.js': 'js/fontawesome-free.all.min.js',
    '@fortawesome/fontawesome-free/css/all.min.css': 'css/fontawesome-free.all.min.css',
    'jquery/dist/jquery.min.js': 'js/jquery.min.js',
    'datatables.net/js/jquery.dataTables.min.js': 'js/jquery.dataTables.min.js',
    'datatables.net-bs4/js/dataTables.bootstrap4.min.js': 'js/dataTables.bootstrap4.min.js',
    'datatables.net-bs4/css/dataTables.bootstrap4.min.css': 'css/dataTables.bootstrap4.min.css',
    'underscore/underscore-min.js': 'js/underscore.min.js',
    'bootstrap/dist/js/bootstrap.bundle.min.js': 'js/bootstrap.bundle.min.js',
    'bootstrap/dist/css/bootstrap.min.css': 'css/bootstrap.min.css',
    'select2/dist/js/select2.full.js': 'js/select2.js',
    'select2/dist/css/select2.css': 'css/select2.css',
    'filepond/dist/filepond.min.js': 'js/filepond.min.js',
    'filepond/dist/filepond.min.css': 'css/filepond.min.css',
    'jsoneditor/dist/jsoneditor.min.js': 'js/jsoneditor.min.js',
    'jsoneditor/dist/jsoneditor.min.css': 'css/jsoneditor.min.css',
    'jsoneditor/dist/img/jsoneditor-icons.svg': 'css/img/jsoneditor-icons.svg',
    'bootbox/bootbox.min.js': 'js/bootbox.min.js',
    'jsonform/lib/jsonform.js': 'js/jsonform.js',
};


TARGETS.forEach((target) => fs.ensureDirSync(path.resolve(__dirname, target), {recursive: true}))

_.each(ASSETS, (target, source) => fs.copyFileSync(path.resolve(__dirname, `./node_modules/${source}`),
    path.resolve(__dirname, `./ui/static/vendors/${target}`)));

// special packages
fs.copySync(path.resolve(__dirname, `./node_modules/@fortawesome/fontawesome-free/webfonts/`),
    path.resolve(__dirname, `./ui/static/vendors/webfonts/`));
