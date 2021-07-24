from inspect import isclass, signature
from masoniteorm import Model

from .AuthorizationResponse import AuthorizationResponse


class Gate:
    def __init__(
        self,
        application,
        user_callback=None,
        policies={},
        permissions={},
        before_callbacks=[],
        after_callbacks=[],
    ):
        self.application = application
        self.user_callback = user_callback

        self.policies = policies
        self.permissions = permissions
        self.before_callbacks = before_callbacks
        self.after_callbacks = after_callbacks

    def define(self, permission, condition):
        if not callable(condition):
            raise Exception(f"Permission {permission} should be given a callable.")

        self.permissions.update({permission: condition})

    def register_policies(self, policies):
        for model_class, policy_class in policies:
            self.policies[model_class] = policy_class
        return self

    def get_policy_for(self, instance):
        if isinstance(instance, Model):
            policy = self.policies.get(instance.__class__, None)
        elif isclass(instance):
            policy = self.policies.get(instance, None)
        elif isinstance(instance, str):
            # TODO: load model from str, get class and get policies
            policy = None
        if policy:
            return policy()
        else:
            return None

    def before(self, before_callback):
        if not callable(before_callback):
            raise Exception("before() should be given a callable.")
        self.before_callbacks.append(before_callback)

    def after(self, after_callback):
        if not callable(after_callback):
            raise Exception("before() should be given a callable.")
        self.after_callbacks.append(after_callback)

    def allows(self, permission, *args):
        return self.inspect(permission, *args).allowed()

    def denies(self, permission, *args):
        return not self.inspect(permission, *args).allowed()

    def has(self, permission):
        return permission in self.permissions

    def for_user(self, user):
        return Gate(
            self.application,
            lambda: user,
            self.policies,
            self.permissions,
            self.before_callbacks,
            self.after_callbacks,
        )

    def any(self, permissions, *args):
        """Check that every of those permissions are allowed."""
        for permission in permissions:
            if self.denies(permission, *args):
                return False
        return True

    def none(self, permissions, *args):
        """Check that none of those permissions are allowed."""
        for permission in permissions:
            if self.allows(permission, *args):
                return False
        return True

    def authorize(self, permission, *args):
        return self.inspect(permission, *args).authorize()

    def inspect(self, permission, *args):
        """Get permission checks results for the given user then builds and returns an
        authorization response."""
        boolean_result = self.check(permission, *args)
        if isinstance(boolean_result, AuthorizationResponse):
            return boolean_result
        if boolean_result:
            return AuthorizationResponse.allow()
        else:
            return AuthorizationResponse.deny()

    def check(self, permission, *args):
        """The core of the authorization class. Run before() checks, permission check and then
        after() checks."""
        user = self._get_user()

        # run before checks and returns immediately if non null response
        result = None
        for callback in self.before_callbacks:
            result = callback(user, permission)
            if result:
                break

        # run permission checks if nothing returned previously
        if result is None:
            # first check in policy
            permission_method = None
            if len(args) > 0:
                policy = self.get_policy_for(args[0])
                if policy:
                    permission_method = getattr(policy, permission)

            if not permission_method:
                # else check in gates
                permission_method = self.permissions[permission]

            params = signature(permission_method).parameters
            # check if user parameter is optional (meaning that guests users are allowed)
            if (
                permission_method.__defaults__
                and permission_method.__defaults__[0] is None
                and not user
            ):
                result = True
            elif not user:
                result = False
            elif len(params) == 1:
                result = permission_method(user)
            else:
                result = permission_method(user, *args)

        # run after checks
        for callback in self.after_callbacks:
            after_result = callback(user, permission, result)
            result = after_result if after_result is not None else result

        return result

    def _get_user(self):
        from ..facades import Request

        if self.user_callback:
            return self.user_callback()
        else:
            return Request.user()
