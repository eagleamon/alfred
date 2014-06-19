'use strict';

var gulp = require('gulp'),
    p = require('gulp-load-plugins')(),

    path = {
        src: {
            jade: 'app/jades/**/*.jade',
            views: 'app/views/**/*.html',
            images: 'app/images/**/*',
            scripts: ['app/scripts/**/*.js', 'gulpfile.js'],
            styles: 'app/styles/**/*.css',
            index: 'app/index.html',
            assets: ['app/favicon.png', 'app/robots.txt'],
        },
        dst: {
            jade: 'app/views/',
            views: '',
            images: 'dist/images/',
            assets: 'dist'
        }
    };

gulp.task('clean', function() {
    return gulp.src('dist', {
            read: false
        })
        .pipe(p.clean());
});

gulp.task('scripts', function() {
    return gulp.src(path.src.scripts)
        .pipe(p.cached())
        .pipe(p.jshint())
        .pipe(p.jshint.reporter('jshint-stylish'));
});

gulp.task('styles', function() {
    return gulp.src(path.src.styles)
        .pipe(p.cached())
        .pipe(p.csslint())
        .pipe(p.csslint.reporter());
});

gulp.task('jade', function() {
    return gulp.src(path.src.jade)
        .pipe(p.cached())
        .pipe(p.filesize())
        .pipe(p.jade({
            pretty: true
        }))
        .pipe(p.filesize())
        .pipe(gulp.dest(path.dst.jade));
});

gulp.task('images', function() {
    return gulp.src(path.src.images)
        .pipe(p.imagemin({
            optimizationLevel: 3,
            progressive: true,
            interlaced: true
        }))
        .pipe(p.filesize())
        .on('error', p.util.log)
        .pipe(gulp.dest(path.dst.images));
});

gulp.task('copy', function() {
    return gulp.src(path.src.assets)
        .pipe(p.filesize())
        .pipe(gulp.dest(path.dst.assets));
});

gulp.task('useref', function() {
    return gulp.src(path.src.index)
        .pipe(p.useref.assets())
        .pipe(p.if('**/styles.css', p.autoprefixer()))
        .pipe(p.if('*.css', p.minifyCss()))
        .pipe(p.if('*.js', p.uglify()))
        .pipe(p.useref.restore())
        .pipe(p.useref())
        .pipe(p.if('*.html', p.minifyHtml({
            conditionals: true
        })))
        .pipe(p.filesize())
        .pipe(gulp.dest('dist'));
});

gulp.task('default', ['dev']);
gulp.task('dev', ['scripts', 'styles', 'jade', 'watch']);
gulp.task('build', ['clean', 'images', 'useref', 'copy']);


var change = function(ev) {
    console.log(ev.path + ' ' + ev.type);
    p.livereload.changed(ev.path);
};

gulp.task('watch', function() {
    p.livereload.listen();
    // p.open('', {url: 'http://localhost:8000'})
    gulp.src(path.src.index).pipe(p.open('', {
        url: 'http://localhost:8000'
    }));
    gulp.watch(path.src.scripts, ['scripts']).on('change', change);
    gulp.watch(path.src.jade, ['jade']).on('change', change);
    gulp.watch(path.src.styles, ['styles']).on('change', change);

});
