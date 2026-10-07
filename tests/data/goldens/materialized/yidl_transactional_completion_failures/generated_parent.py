from __future__ import annotations
import weakref
from yidl_lifecycle.lifecycle import _HAS_DEFAULT_FACTORY
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION
from yidl_lifecycle.transaction_yidl import TransactionManager
VOID = object()

def build_lifecycle_class(decorated_cls, *, _CompletionParent_lifecycle_definition, _CompletionParent_annotations, _CompletionParent_tx_keys, _CompletionParent_rank_default, _CompletionParent_control_default, _CompletionParent_count_default, _CompletionParent_count_freeze, _CompletionParent_untouched_default, _CompletionParent_items_default, _CompletionParent_items_freeze, _CompletionParent_items_thaw, _CompletionParent_scratch_default, _CompletionParent_scratch_working_default_factory, _CompletionParent_resource_default, _CompletionParent_audit_default):
    from collections.abc import Mapping
    from yidl_lifecycle.bindings import BindingBase, BindingDict

    def _y_validate_binding_value(field_name, value):
        if value is not None and (not isinstance(value, BindingBase)):
            raise TypeError('binding field ' + repr(field_name) + ' expects BindingBase or None')
        return value

    def _y_validate_binding_map_value(field_name, value):
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise TypeError('binding map field ' + repr(field_name) + ' expects a mapping or None')
        result = value if isinstance(value, BindingDict) else BindingDict(value)
        for key, item in result.items():
            if not isinstance(item, BindingBase):
                raise TypeError('binding map field ' + repr(field_name) + ' expects BindingBase values; key ' + repr(key) + ' has ' + type(item).__name__)
        return result

    class CompletionParent_State:
        __slots__ = ('_y_transaction_manager', '_y_default_ref', '_y_current_ref', '_y_working_ref', '_y_rank_value', '_y_control_value', '_y_count_current', '_y_count_working', '_y_count_staged', '_y_untouched_current', '_y_untouched_working', '_y_untouched_staged', '_y_items_current', '_y_items_working', '_y_items_staged', '_y_scratch_current', '_y_scratch_working', '_y_resource_current', '_y_resource_working', '_y_resource_staged', '_y_audit_current', '_y_audit_working', '_y_audit_staged', '_y_working_tx_ids')
        __yidl_tx_index_to_key__ = _CompletionParent_tx_keys
        __yidl_tx_key_to_index__ = {key: index for index, key in enumerate(_CompletionParent_tx_keys)}

        def _y_get_default_facade(self):
            ref = self._y_default_ref
            facade = None if ref is None else ref()
            if facade is None:
                facade = object.__new__(CompletionParent)
                object.__setattr__(facade, '_y_state', self)
                current_ref = self._y_current_ref
                working_ref = self._y_working_ref
                object.__setattr__(facade, '_y_current_facade', None if current_ref is None else current_ref())
                object.__setattr__(facade, '_y_working_facade', None if working_ref is None else working_ref())
                self._y_default_ref = weakref.ref(facade)
            return facade

        def _y_get_current_facade(self):
            ref = self._y_current_ref
            facade = None if ref is None else ref()
            if facade is None:
                facade = object.__new__(CompletionParent_Current)
                object.__setattr__(facade, '_y_state', self)
                self._y_current_ref = weakref.ref(facade)
                default_ref = self._y_default_ref
                default = None if default_ref is None else default_ref()
                if default is not None:
                    object.__setattr__(default, '_y_current_facade', facade)
            return facade

        def _y_get_working_facade(self):
            ref = self._y_working_ref
            facade = None if ref is None else ref()
            if facade is None:
                facade = object.__new__(CompletionParent_Working)
                object.__setattr__(facade, '_y_state', self)
                self._y_working_ref = weakref.ref(facade)
                default_ref = self._y_default_ref
                default = None if default_ref is None else default_ref()
                if default is not None:
                    object.__setattr__(default, '_y_working_facade', facade)
            return facade

        def _y_require_active_transaction(self, tx_index):
            tx_key = self.__yidl_tx_index_to_key__[tx_index]
            transaction = self._y_transaction_manager.active_transaction_for(tx_key)
            if transaction is None:
                if self._y_working_tx_ids[tx_index] is not None:
                    raise RuntimeError('stale yidl working value without an active transaction')
                raise RuntimeError('writes require an active yidl transaction')
            self._y_transaction_manager._require_candidate_write(self, tx_key)
            existing_tx_id = self._y_working_tx_ids[tx_index]
            if existing_tx_id is not None and existing_tx_id != transaction.tx_id:
                raise RuntimeError('working value belongs to a different yidl transaction')
            return transaction

        def _y_ensure_working_transaction(self, tx_index):
            transaction = self._y_require_active_transaction(tx_index)
            if self._y_working_tx_ids[tx_index] is None:
                tx_key = self.__yidl_tx_index_to_key__[tx_index]
                self._y_working_tx_ids[tx_index] = self._y_transaction_manager.enlist(self, tx_key)
            return transaction

        def commit_order_key_for(self, tx_key=DEFAULT_TRANSACTION):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            if False:
                pass
            elif tx_index == 0:
                return self._commit_order_key_tx_0()
            elif tx_index == 1:
                return self._commit_order_key_tx_1()
            elif True:
                return ()

        def requires_validation_for(self, tx_key=DEFAULT_TRANSACTION):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            if False:
                pass
            elif tx_index == 0:
                return self._requires_validation_tx_0()
            elif tx_index == 1:
                return self._requires_validation_tx_1()
            elif True:
                return False

        def validate_commit_for(self, tx_key=DEFAULT_TRANSACTION):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            if False:
                pass
            elif tx_index == 0:
                return self._validate_commit_tx_0()
            elif tx_index == 1:
                return self._validate_commit_tx_1()
            elif True:
                return True

        def _prepare_commit_tx_by_key(self, tx_key=DEFAULT_TRANSACTION, tx_token=None):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            if self._y_working_tx_ids[tx_index] != tx_token:
                raise RuntimeError('stale yidl transaction token')
            with self._y_transaction_manager._before_commit_hooks(self, tx_key, tx_token):
                if False:
                    pass
                elif tx_index == 0:
                    self._before_commit_tx_0()
                elif tx_index == 1:
                    self._before_commit_tx_1()
                elif True:
                    pass
            if False:
                pass
            elif tx_index == 0:
                self._prepare_commit_tx_0_fields()
            elif tx_index == 1:
                self._prepare_commit_tx_1_fields()
            elif True:
                pass
            return self._y_get_default_facade()

        def _apply_prepared_commit_tx_by_key(self, tx_key=DEFAULT_TRANSACTION, tx_token=None):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            if self._y_working_tx_ids[tx_index] != tx_token:
                raise RuntimeError('stale yidl transaction token')
            if False:
                pass
            elif tx_index == 0:
                self._apply_prepared_commit_tx_0_fields()
            elif tx_index == 1:
                self._apply_prepared_commit_tx_1_fields()
            elif True:
                pass
            self._y_working_tx_ids[tx_index] = None
            return self._y_get_default_facade()

        def _after_commit_tx_by_key(self, tx_key=DEFAULT_TRANSACTION, tx_token=None):
            del tx_token
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            failures = []
            if False:
                pass
            elif tx_index == 0:
                self._after_commit_tx_0()
            elif tx_index == 1:
                self._after_commit_tx_1()
            elif True:
                pass
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-commit hooks failed', failures)
            return self._y_get_default_facade()

        def _rollback_tx_by_key(self, tx_key=DEFAULT_TRANSACTION, tx_token=None):
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            del tx_token
            if False:
                pass
            elif tx_index == 0:
                self._rollback_tx_0_fields()
            elif tx_index == 1:
                self._rollback_tx_1_fields()
            elif True:
                pass
            self._y_working_tx_ids[tx_index] = None
            return self._y_get_default_facade()

        def _after_rollback_tx_by_key(self, tx_key=DEFAULT_TRANSACTION, tx_token=None):
            del tx_token
            tx_index = self.__yidl_tx_key_to_index__[tx_key]
            failures = []
            if False:
                pass
            elif tx_index == 0:
                self._after_rollback_tx_0()
            elif tx_index == 1:
                self._after_rollback_tx_1()
            elif True:
                pass
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-rollback hooks failed', failures)
            return self._y_get_default_facade()

        def _commit_order_key_tx_0(self):
            return self._y_get_default_facade()._order()

        def _requires_validation_tx_0(self):
            return True

        def _validate_commit_tx_0(self):
            result = self._y_get_default_facade()._validate()
            if not result:
                return result
            return True

        def _before_commit_tx_0(self):
            self._y_get_default_facade()._before()

        def _after_commit_tx_0(self):
            failures = []
            try:
                self._y_get_default_facade()._parent_after_commit()
            except BaseException as error:
                failures.append(error)
                try:
                    BaseException.add_note(error, '_parent_after_commit')
                except BaseException:
                    pass
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-commit hooks failed', failures)

        def _apply_prepared_commit_tx_0_fields(self):
            if self._y_count_staged is not VOID:
                self._y_count_current = self._y_count_staged
                self._y_count_staged = VOID
                self._y_count_working = VOID
            if self._y_untouched_staged is not VOID:
                self._y_untouched_current = self._y_untouched_staged
                self._y_untouched_staged = VOID
                self._y_untouched_working = VOID
            if self._y_items_staged is not VOID:
                self._y_items_current = self._y_items_staged
                self._y_items_staged = VOID
                self._y_items_working = VOID
            self._y_scratch_working = VOID
            if self._y_resource_staged is not VOID:
                self._y_resource_current = self._y_resource_staged
                self._y_resource_staged = VOID
                self._y_resource_working = VOID

        def _prepare_commit_tx_0_fields(self):
            if self._y_count_working is not VOID:
                self._y_count_staged = _CompletionParent_count_freeze(self._y_count_working)
            if self._y_untouched_working is not VOID:
                self._y_untouched_staged = self._y_untouched_working
            if self._y_items_working is not VOID:
                self._y_items_staged = _CompletionParent_items_freeze(self._y_items_working)
            if self._y_resource_working is not VOID:
                value = self._y_resource_working
                if value is not None:
                    value.accepted()
                self._y_resource_staged = value

        def _commit_order_key_tx_1(self):
            return ()

        def _requires_validation_tx_1(self):
            return False

        def _validate_commit_tx_1(self):
            return True

        def _before_commit_tx_1(self):
            pass

        def _after_commit_tx_1(self):
            failures = []
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-commit hooks failed', failures)

        def _apply_prepared_commit_tx_1_fields(self):
            if self._y_audit_staged is not VOID:
                self._y_audit_current = self._y_audit_staged
                self._y_audit_staged = VOID
                self._y_audit_working = VOID

        def _prepare_commit_tx_1_fields(self):
            if self._y_audit_working is not VOID:
                self._y_audit_staged = self._y_audit_working

        def _after_rollback_tx_0(self):
            failures = []
            try:
                self._y_get_default_facade()._parent_after_rollback()
            except BaseException as error:
                failures.append(error)
                try:
                    BaseException.add_note(error, '_parent_after_rollback')
                except BaseException:
                    pass
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-rollback hooks failed', failures)

        def _rollback_tx_0_fields(self):
            self._y_count_staged = VOID
            self._y_count_working = VOID
            self._y_untouched_staged = VOID
            self._y_untouched_working = VOID
            self._y_items_staged = VOID
            self._y_items_working = VOID
            self._y_scratch_working = VOID
            self._y_resource_staged = VOID
            self._y_resource_working = VOID

        def _after_rollback_tx_1(self):
            failures = []
            if len(failures) == 1:
                raise failures[0]
            if failures:
                raise BaseExceptionGroup('yidl after-rollback hooks failed', failures)

        def _rollback_tx_1_fields(self):
            self._y_audit_staged = VOID
            self._y_audit_working = VOID

    class CompletionParent_FacadeBase(decorated_cls):
        __slots__ = ('_y_state',) if hasattr(decorated_cls, '__weakref__') else ('_y_state', '__weakref__')
        _y_lifecycle_field_names = frozenset(('rank', 'control', 'count', 'untouched', 'items', 'scratch', 'resource', 'audit'))

        def __setattr__(self, name, value):
            if name in self._y_lifecycle_field_names:
                descriptor = getattr(type(self), name, None)
                if descriptor is None or not hasattr(descriptor, '__set__'):
                    raise AttributeError(f'lifecycle field {name!r} is not assignable')
                descriptor.__set__(self, value)
                return
            if name.startswith('_y_') or name.startswith('__yidl_'):
                raise AttributeError(f'{name!r} is reserved for generated lifecycle state')
            object.__setattr__(self, name, value)

        def __delattr__(self, name):
            if name in self._y_lifecycle_field_names:
                raise AttributeError(f'lifecycle field {name!r} cannot be deleted')
            if name.startswith('_y_') or name.startswith('__yidl_'):
                raise AttributeError(f'{name!r} is reserved for generated lifecycle state')
            object.__delattr__(self, name)

        @property
        def default(self):
            return self._y_state._y_get_default_facade()

        @property
        def current(self):
            return self._y_state._y_get_current_facade()

        @property
        def working(self):
            return self._y_state._y_get_working_facade()

        def _y_get_transaction_manager(self):
            return self._y_state._y_transaction_manager

        def begin(self, *tx_keys):
            return self._y_get_transaction_manager().begin(*tx_keys)

        def validate(self, *tx_keys):
            return self._y_get_transaction_manager().validate(*tx_keys)

        def commit_only(self, *tx_keys):
            return self._y_get_transaction_manager().commit_only(*tx_keys)

        def commit(self, *tx_keys):
            return self._y_get_transaction_manager().commit(*tx_keys)

        def rollback(self, *tx_keys):
            return self._y_get_transaction_manager().rollback(*tx_keys)

        @property
        def rank(self):
            return self._y_state._y_rank_value

        @rank.setter
        def rank(self, value):
            self._y_state._y_rank_value = value

        @property
        def control(self):
            return self._y_state._y_control_value

        @control.setter
        def control(self, value):
            self._y_state._y_control_value = value

    class CompletionParent(CompletionParent_FacadeBase):
        __slots__ = ('_y_current_facade', '_y_working_facade')
        __annotations__ = _CompletionParent_annotations
        __yidl_lifecycle_generated__ = True
        __yidl_lifecycle_user_class__ = decorated_cls
        __yidl_lifecycle_definition__ = _CompletionParent_lifecycle_definition
        __yidl_tx_index_to_key__ = _CompletionParent_tx_keys
        __yidl_tx_key_to_index__ = {key: index for index, key in enumerate(_CompletionParent_tx_keys)}

        @property
        def count(self):
            state = self._y_state
            if state._y_count_working is not VOID:
                return state._y_count_working
            return state._y_count_current

        @count.setter
        def count(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_count_working is not VOID:
                current = state._y_count_working
            else:
                current = state._y_count_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_count_working = next_value

        @property
        def untouched(self):
            state = self._y_state
            if state._y_untouched_working is not VOID:
                return state._y_untouched_working
            return state._y_untouched_current

        @untouched.setter
        def untouched(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_untouched_working is not VOID:
                current = state._y_untouched_working
            else:
                current = state._y_untouched_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_untouched_working = next_value

        @property
        def items(self):
            state = self._y_state
            if state._y_items_working is not VOID:
                return state._y_items_working
            return state._y_items_current

        @items.setter
        def items(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_items_working is not VOID:
                current = state._y_items_working
            else:
                current = state._y_items_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_items_working = next_value

        @property
        def scratch(self):
            state = self._y_state
            if state._y_scratch_working is not VOID:
                return state._y_scratch_working
            tx_key = state.__yidl_tx_index_to_key__[0]
            if state._y_transaction_manager.active_transaction_for(tx_key) is None:
                return state._y_scratch_current
            state._y_ensure_working_transaction(0)
            state._y_scratch_working = _CompletionParent_scratch_working_default_factory()
            return state._y_scratch_working

        @scratch.setter
        def scratch(self, value):
            state = self._y_state
            state._y_ensure_working_transaction(0)
            state._y_scratch_working = value

        @property
        def resource(self):
            state = self._y_state
            if state._y_resource_working is not VOID:
                return state._y_resource_working
            return state._y_resource_current

        @resource.setter
        def resource(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            next_value = _y_validate_binding_value('resource', value)
            if state._y_resource_working is not VOID:
                current = state._y_resource_working
            else:
                current = state._y_resource_current
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_resource_working = next_value

        @property
        def audit(self):
            state = self._y_state
            if state._y_audit_working is not VOID:
                return state._y_audit_working
            return state._y_audit_current

        @audit.setter
        def audit(self, value):
            state = self._y_state
            state._y_require_active_transaction(1)
            if state._y_audit_working is not VOID:
                current = state._y_audit_working
            else:
                current = state._y_audit_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(1)
            state._y_audit_working = next_value

        def __init__(self, rank: 'int'=_CompletionParent_rank_default, control: 'object'=_CompletionParent_control_default, count: 'int'=_CompletionParent_count_default, untouched: 'int'=_CompletionParent_untouched_default, items: 'tuple[int, ...]'=_CompletionParent_items_default, scratch: 'list[int] | None'=_CompletionParent_scratch_default, resource: 'BindingBase | None'=_CompletionParent_resource_default, audit: 'int'=_CompletionParent_audit_default, *, transaction_manager=None):
            state = object.__new__(CompletionParent_State)
            object.__setattr__(self, '_y_state', state)
            object.__setattr__(self, '_y_current_facade', None)
            object.__setattr__(self, '_y_working_facade', None)
            state._y_transaction_manager = transaction_manager or TransactionManager(tx_keys=tuple((group for group in _CompletionParent_tx_keys if group != DEFAULT_TRANSACTION)))
            state._y_default_ref = weakref.ref(self)
            state._y_current_ref = None
            state._y_working_ref = None
            state._y_rank_value = rank
            state._y_control_value = control
            state._y_count_current = count
            state._y_count_working = VOID
            state._y_count_staged = VOID
            state._y_untouched_current = untouched
            state._y_untouched_working = VOID
            state._y_untouched_staged = VOID
            state._y_items_current = items
            state._y_items_working = VOID
            state._y_items_staged = VOID
            state._y_scratch_current = scratch
            state._y_scratch_working = VOID
            value = _y_validate_binding_value('resource', resource)
            state._y_resource_current = value
            state._y_resource_working = VOID
            state._y_resource_staged = VOID
            state._y_audit_current = audit
            state._y_audit_working = VOID
            state._y_audit_staged = VOID
            state._y_working_tx_ids = [None for _group in _CompletionParent_tx_keys]

    class CompletionParent_Current(CompletionParent_FacadeBase):
        __slots__ = ()

        @property
        def count(self):
            return self._y_state._y_count_current

        @count.setter
        def count(self, value):
            del value
            raise AttributeError('current facade is read-only for transactional field ' + 'count')

        @property
        def untouched(self):
            return self._y_state._y_untouched_current

        @untouched.setter
        def untouched(self, value):
            del value
            raise AttributeError('current facade is read-only for transactional field ' + 'untouched')

        @property
        def items(self):
            return self._y_state._y_items_current

        @items.setter
        def items(self, value):
            del value
            raise AttributeError('current facade is read-only for transactional field ' + 'items')

        @property
        def scratch(self):
            return self._y_state._y_scratch_current

        @property
        def resource(self):
            return self._y_state._y_resource_current

        @resource.setter
        def resource(self, value):
            del value
            raise AttributeError('current facade is read-only for owned field ' + 'resource')

        @property
        def audit(self):
            return self._y_state._y_audit_current

        @audit.setter
        def audit(self, value):
            del value
            raise AttributeError('current facade is read-only for transactional field ' + 'audit')

    class CompletionParent_Working(CompletionParent_FacadeBase):
        __slots__ = ()

        @property
        def count(self):
            state = self._y_state
            if state._y_count_working is not VOID:
                return state._y_count_working
            return state._y_count_current

        @count.setter
        def count(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_count_working is not VOID:
                current = state._y_count_working
            else:
                current = state._y_count_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_count_working = next_value

        @property
        def untouched(self):
            state = self._y_state
            if state._y_untouched_working is not VOID:
                return state._y_untouched_working
            return state._y_untouched_current

        @untouched.setter
        def untouched(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_untouched_working is not VOID:
                current = state._y_untouched_working
            else:
                current = state._y_untouched_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_untouched_working = next_value

        @property
        def items(self):
            state = self._y_state
            if state._y_items_working is not VOID:
                return state._y_items_working
            tx_key = state.__yidl_tx_index_to_key__[0]
            if state._y_transaction_manager.active_transaction_for(tx_key) is None:
                return state._y_items_current
            state._y_ensure_working_transaction(0)
            next_value = _CompletionParent_items_thaw(state._y_items_current)
            state._y_items_working = next_value
            return next_value

        @items.setter
        def items(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            if state._y_items_working is not VOID:
                current = state._y_items_working
            else:
                current = _CompletionParent_items_thaw(state._y_items_current)
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_items_working = next_value

        @property
        def scratch(self):
            state = self._y_state
            if state._y_scratch_working is not VOID:
                return state._y_scratch_working
            tx_key = state.__yidl_tx_index_to_key__[0]
            if state._y_transaction_manager.active_transaction_for(tx_key) is None:
                return state._y_scratch_current
            state._y_ensure_working_transaction(0)
            state._y_scratch_working = _CompletionParent_scratch_working_default_factory()
            return state._y_scratch_working

        @scratch.setter
        def scratch(self, value):
            state = self._y_state
            state._y_ensure_working_transaction(0)
            state._y_scratch_working = value

        @property
        def resource(self):
            state = self._y_state
            if state._y_resource_working is not VOID:
                return state._y_resource_working
            return state._y_resource_current

        @resource.setter
        def resource(self, value):
            state = self._y_state
            state._y_require_active_transaction(0)
            next_value = _y_validate_binding_value('resource', value)
            if state._y_resource_working is not VOID:
                current = state._y_resource_working
            else:
                current = state._y_resource_current
            if current == next_value:
                return
            state._y_ensure_working_transaction(0)
            state._y_resource_working = next_value

        @property
        def audit(self):
            state = self._y_state
            if state._y_audit_working is not VOID:
                return state._y_audit_working
            return state._y_audit_current

        @audit.setter
        def audit(self, value):
            state = self._y_state
            state._y_require_active_transaction(1)
            if state._y_audit_working is not VOID:
                current = state._y_audit_working
            else:
                current = state._y_audit_current
            next_value = value
            if current == next_value:
                return
            state._y_ensure_working_transaction(1)
            state._y_audit_working = next_value
    CompletionParent.__name__ = decorated_cls.__name__
    CompletionParent.__qualname__ = decorated_cls.__qualname__
    CompletionParent.__module__ = decorated_cls.__module__
    return CompletionParent
