'use strict';

var gulp = require('gulp'),
    del = require('del'),
    p = require('gulp-load-plugins')(),

    path = {
        src: {
            app: 'app',
            jade: 'app/**/*.jade',
            views: 'app/views/**/*.html',
            images: 'app/images/**/*',
            scripts: 'app/scripts/**/*.js',
            styles: 'app/styles/**/*.css',
            jadeIndex: 'app/index.jade',
            index: 'app/index.html',
            assets: ['app/favicon.png', 'app/robots.txt'],
        },
        dst: {
            app: 'app',
            jade: 'app/views/',
            views: '',
            images: 'dist/images/',
            assets: 'dist'
        }
    };

gulp.task('scripts', function() {
    return p.watch([path.src.scripts, './gulpfile.js'])
        .pipe(p.cached())
        .pipe(p.filesize())
        .pipe(p.jshint())
        .pipe(p.jshint.reporter('jshint-stylish')
        .pipe(p.livereload()));
});

gulp.task('jade', function(){
    return p.watch([path.src.jade])
        .pipe(p.cached())
        .pipe(p.filesize())
        .pipe(p.jade({
            pretty: true
        }))
        .pipe(p.filesize())
        .pipe(gulp.dest(path.dst.app))
        .pipe(p.livereload())
})

gulp.task('clean', function(){
    del(['.app', 'dist']);
});

// gulp.task('scripts', function() {
//     return gulp.src([path.src.scripts, './gulpfile.js'])
//         .pipe(p.cached())
//         .pipe(p.filesize())
//         .pipe(p.jshint())
//         .pipe(p.jshint.reporter('jshint-stylish'));
// });

gulp.task('styles', function() {
    return p.watch(path.src.styles)
        .pipe(p.cached())
        .pipe(p.filesize())
        .pipe(p.csslint())
        .pipe(p.csslint.reporter())
        .pipe(p.livereload());
});

// gulp.task('jade', function() {
//     return gulp.src(path.src.jade)
//         .pipe(p.cached())
//         .pipe(p.filesize())
//         .pipe(p.jade({
//             pretty: true
//         }))
//         .pipe(p.filesize())
//         // Add a rename, as for scss etc to prevent versioning of the result: ae.scss.css or aeze.jade.html
//         .pipe(gulp.dest(path.dst.jade));
// });

// gulp.task('jadeIndex', function(){
//     return gulp.src(path.src.jadeIndex)
//         .pipe(p.cached())
//         .pipe(p.jade({pretty:true}))
//         .pipe(gulp.dest(path.src.app));
// });

// gulp.task('images', function() {
//     return gulp.src(path.src.images)
//         .pipe(p.imagemin({
//             optimizationLevel: 3,
//             progressive: true,
//             interlaced: true
//         }))
//         .pipe(p.filesize())
//         .on('error', p.util.log)
//         .pipe(gulp.dest(path.dst.images));
// });

// gulp.task('copy', function() {
//     return gulp.src(path.src.assets)
//         .pipe(p.filesize())
//         .pipe(gulp.dest(path.dst.assets));
// });

// gulp.task('useref', function() {
//     return gulp.src(path.src.index)
//         .pipe(p.useref.assets())
//         .pipe(p.if('**/styles.css', p.autoprefixer()))
//         .pipe(p.if('*.css', p.minifyCss()))
//         .pipe(p.if('*.js', p.uglify()))
//         .pipe(p.useref.restore())
//         .pipe(p.useref())
//         // .pipe(p.if('*.html', p.minifyHtml({
//         //     conditionals: true
//         // })))
//         .pipe(p.filesize())
//         .pipe(gulp.dest('dist'));
// });

// gulp.task('ng', function(){
//     return gulp.src(path.src.scripts)
//         .pipe(p.filesize())
//         .pipe(p.ngmin())
//         .pipe(p.filesize())
//         .pipe(gulp.dest('dist/'));
// });

gulp.task('lr', function(){
    p.livereload.listen();
});

gulp.task('default', ['lr', 'dev']);
gulp.task('dev', ['scripts', 'jade', 'styles']);
// gulp.task('dev', ['scripts', 'styles', 'jadeIndex', 'jade', 'watch']);
// gulp.task('build', ['clean', 'images', 'useref', 'copy']);


// var change = function(ev) {
//     console.log('Changed: ' +ev.path + ' ' + ev.type);
//     p.livereload.changed();
// };

// gulp.task('watch', function() {
//     p.livereload.listen();
//     // p.open('', {url: 'http://localhost:8000'})
//     // gulp.src(path.src.index).pipe(p.open('', {
//     //     url: 'http://localhost:8000'
//     // }));
//     gulp.watch([path.src.scripts, './gulpfile.js'], ['scripts']).on('change', change);
//     gulp.watch(path.src.jade, ['jade']).on('change', change);
//     gulp.watch(path.src.jadeIndex, ['jadeIndex']).on('change', change);
//     gulp.watch(path.src.styles, ['styles']);
// });
