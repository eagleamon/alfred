'use strict';

var alfred = angular.module('alfred',   ['ngRoute', 'ngResource', 'ngCookies', 'ngAnimate', 'ui.bootstrap', 'highcharts-ng', 'angularMoment', 'ui.select2'])
    .config(['$routeProvider', '$httpProvider',
        function($routeProvider, $httpProvider) {
            $routeProvider
                .when('/hmi', {
                    templateUrl: 'views/hmi.html',
                    controller: 'HmiCtrl'
                })
                .when('/items', {
                    templateUrl: 'views/items.html',
                    controller: 'ItemsCtrl'
                })
                .when('/editItem', {
                    templateUrl: 'views/editItem.html',
                    controller: 'EditItemCtrl'
                })
                .when('/editItem/:_id', {
                    templateUrl: 'views/editItem.html',
                    controller: 'EditItemCtrl'
                })
                .when('/graph/:_id', {
                    templateUrl: 'views/graph.html',
                    controller: 'GraphCtrl'
                })
                .when('/cameras',   {
                    templateUrl: 'views/cameras.html',
                })
                .when('/plugins', {
                    templateUrl: 'views/plugins.html',
                    controller: 'PluginCtrl'
                })
                .when('/config', {
                    templateUrl: 'views/config.html',
                    controller: 'ConfigCtrl'
                })
                .when('/login', {
                    templateUrl: 'views/login.html',
                    controller: 'LoginCtrl'
                })
                .otherwise({
                    redirectTo: '/hmi'
                });


            // If the server needs an authentication, redirect to the login page
            $httpProvider.interceptors.push(function($q, $location) {
                return {
                    'responseError': function(rejection) {
                        if (rejection.status === 401)
                            $location.path('/login');
                        return $q.reject(rejection);
                    }
                };
            });

        }
    ])

.factory('WebSocket', function($rootScope, $log) {
    return {
        connect: function() {
            var $this = this;
            console.info('Trying to connect to WebSocket..');
            var socket = new WebSocket('ws://' + location.host + '/live');
            socket.onopen = function() {
                console.info('Socket connected!');
                $rootScope.$broadcast('websocket:connected');
            };
            socket.onerror = function(event) {
                console.info('WebSocket error: ' + event);
            };
            socket.onclose = function(event) {
                $rootScope.$broadcast('websocket:disconnected');
                console.error('Socket closed, reconnecting in 5 seconds... ' + (event.reason ? '(' + event.reason + ')' : ''));
                setTimeout(function() {
                    $this.connect();
                }, 5000);
            };
            socket.onmessage = function(msg) {
                msg = JSON.parse(msg.data);
                if (msg.level) {
                    var tmp = msg.host + '@:' + msg.time + ' - ' + msg.message;
                    if (msg.level === 'DEBUG')
                        $log.debug(tmp);
                    else if (msg.level === 'INFO')
                        $log.info(tmp);
                    else if (msg.level === 'WARN')
                        $log.warn(tmp);
                    else
                        $log.error(tmp);
                } else {
                    $rootScope.$apply(
                        $this.onmessage(msg)
                    );
                }
            };
        },
        // onmessage: function(callback) {}
    };
})

// Service to handle atuthentication against backend validation
.factory('Auth', function($http, $location, $rootScope) { //$cookieStore
    return {
        user: {
            username: ''
        },
        login: function(username, password) {
            var $this = this;
            return $http.post('/auth/login', {
                    username: username,
                    password: password
                })
                .success(function() {
                    $this.user.username = username;
                    $rootScope.$broadcast('auth:login', $this.user);
                });
        },
        logout: function() {
            var $this = this;
            $http.get('/auth/logout')
                .success(function() {
                    $this.user.username = null;
                    $rootScope.$broadcast('auth:logout');
                    $location.path('/');
                });
        }
    };
})

// Simple service to handle the alerts
.factory('AlertService', function($timeout) {
    return {
        alerts: [],

        add: function(alert) {
            var $this = this;
            this.alerts.push(alert);
            if ('timeout' in alert) {
                $timeout(function() {
                    $this.close($this.alerts.length - 1);
                }, alert.timeout);
            }
        },

        close: function(index) {
            this.alerts.splice(index, 1);
        }
    };
})

.factory('Item', function($resource) {
    return $resource('/api/v1/item/:_id', {
        _id: '@_id.$oid'
    }, {
        update: {
            method: 'PUT'
        }
    });
})

.factory('Config', function($resource) {
    return $resource('/api/v1/config', {}, {
        update: {
            method: 'PUT'
        }
    });
})

.factory('Commands', function($http, $log) {
    return {
        send: function(itemName, command) {
            $log.info('Sending ' + command + ' to ' + itemName);
            $http.post('/api/v1/item/' + itemName + '/command/' + command.toLowerCase());
        }
    };
})

// Can't map directly to REST as plugins are part of config by host and config for all hosts like items exists
.factory('Plugin', function($http) {
    return {
        query: function() {
            return $http.get('/api/v1/plugin');
        },
        start: function(name) {
            return $http.post('/api/v1/plugin/' + name + '/start');
        },
        stop: function(name) {
            return $http.post('/api/v1/plugin/' + name + '/stop');
        },
        install: function(name) {
            return $http.post('/api/v1/plugin/' + name + '/install');
        },
        uninstall: function(name) {
            return $http.post('/api/v1/plugin/' + name + '/uninstall');
        },
        save: function(name, value) {
            return $http.put('/api/v1/plugin/' + name, {
                'data': {
                    autoStart: value.autoStart,
                    config: value.config
                }
            });
        }
    };
})

.directive('showOnHover', function() {
    return {
        link: function(scope, element) { //, attrs
            element.css('visibility', 'hidden');
            element.parent().parent().bind('mouseenter', function() {
                element.css('visibility', 'visible');
            });
            element.parent().parent().bind('mouseleave', function() {
                element.css('visibility', 'hidden');
            });
        }
    };
})

.directive('switch', function() {
    return {
        restrict: 'E',
        replace: true,
        require: '^ngModel',
        template: '<span class="switch" ng-click="onSwitch()""> {{ngModel}}' +
            '   <span class="background"></span><span class="mask"></span</span>',
        scope: {
            ngModel: '=',
            onSwitch: '&'
        },
        link: function(scope, elem) {
            elem.bind('click', function() {
                if (scope.ngModel)
                    elem.find('.background').animate({
                        left: '-57px'
                    }, 200);
                else
                    elem.find('.background').animate({
                        left: '0px'
                    }, 200);
            });
            scope.$watch('ngModel', function(val) {
                if (val)
                    elem.find('.background').animate({
                        left: '0px'
                    }, 200);
                else
                    elem.find('.background').animate({
                        left: '-57px'
                    }, 200);
            });
        },
    };
})

.directive('websocketstatus', function() {
    return {
        restrict: 'EA',
        template: '<span>{{state}}</span>',
        scope: {},
        link: function(scope) {
            scope.state = 'ok';
        },
        controller: function($scope) {
            $scope.$on('websocket:connected', function() {
                $scope.$apply(function() {
                    $scope.state = 'Connected';
                });
            });
            $scope.$on('websocket:disconnected', function() {
                $scope.$apply(function() {
                    $scope.state = 'Connecting...';
                });
            });
        }
    };
})

.filter('title', function() {
    return function(str) {
        return str ? str[0].toUpperCase() + str.substring(1, str.length) : '';
    };
})

// Simple filter to overcome the limitation of filtering objects of object
.filter('array', function() {
    return function(items) {
        var filtered = [];
        angular.forEach(items, function(item) {
            filtered.push(item);
        });
        return filtered;
    };
});

alfred.run(function($rootScope, WebSocket, Auth, $log) {
    Highcharts.setOptions({ // This is for all plots, change Date axis to local timezone
        global: {
            useUTC: false
        }
    });

    $rootScope.$log = $log;
    WebSocket.connect();
});
