def setstorage(cls):
    def decorate(func):
        def call(this, storage = None, *args, **kwargs):
            if hasattr(kwargs, 'storage') and getattr(kwargs, 'storage') is not None:
                assert(isinstance(kwargs['storage'], Storage))
                old_storage = this.storage
                this.storage = kwargs['storage']

            result = func(*args, **kwargs)

            if hasattr(kwargs, 'storage') and getattr(kwargs, 'storage') is not None:
                this.storage = old_storage
            return result
        return call
    return decorate

def defaultstorage(cls):
    def decorate(func):
        def call(*args, **kwargs):
            this = args[0]
            if not hasattr(kwargs, 'storage') or getattr(kwargs, 'storage') is None:
                kwargs['storage'] = this.default_storage

            result = func(*args, **kwargs)
            return result
        return call
    return decorate

def setstorage(list_arg):
    def decorate(func):
        def call(this, *args, **kwargs):
            if hasattr(kwargs, list_arg) and type(getattr(kwargs, list_arg)) is not list:
                kwargs[list_arg] = list(kwargs[list_arg])
                result = func(*args, **kwargs)
                return result[0]
            else:
                return func(*args, **kwargs)
        return call
    return decorate

class ObjectStorage(object):

    def __init__(self, storage, obj):
        self.storage = storage
        self.content_class = obj
        self.idx_dimension = obj.__name__.lower()

    def __call__(self, storage):
        store = copy.deepcopy(self)
        store.storage = storage
        return store

    def save(self, obj, idx=None):
        """
        Add the current state of the trajectory in the database. If nothing has changed then the trajectory gets stored using the same snapshots as before. Saving lots of diskspace

        Parameters
        ----------
        storage : TrajectoryStorage()
            If set this specifies the storage to be used. If the storage is None the default storage is used, which needs to
            be set in advance.

        Notes
        -----
        This also saves all contained frames in the trajectory if not done yet.
        A single Trajectory object can only be saved once!

        """

        storage = self.storage
        if idx is None:
            if storage in obj.idx:
                # has been saved so quit and do nothing
                return None
            else:
                idx = self.free()
                obj.idx[storage] = idx
                return idx
        else:
            return idx

    def load(self, idx, momentum = True):
        '''
        Return a trajectory from the storage

        Parameters
        ----------
        idx : int
            index of the trajectory (counts from 1)

        Returns
        -------
        trajectory : Trajectory
            the trajectory
        '''
        return None

    def get(self, indices):
        return [self.load(idx) for idx in range(0, self.number())[indices] ]


    def last(self):
        '''
        Returns the last generated trajectory. Useful to continue a run.

        Returns
        -------
        Trajectoy
            the actual trajectory object
        '''
        return self.load(self.number())

    def first(self):
        '''
        Returns the last generated trajectory. Useful to continue a run.

        Returns
        -------
        Trajectoy
            the actual trajectory object
        '''
        return self.load(1)

    def number(self):
        '''
        Return the number of trajectories in the storage

        Returns
        -------
        number : int
            number of trajectories in the storage. Their indexing starts with 1.
        '''
        length = int(len(self.storage.dimensions[self.idx_dimension])) - 1
        if length < 0:
            length = 0
        return length


    def free(self):
        '''
        Return the number of the next _free_idx ID

        Returns
        -------
        index : int
            the number of the next _free_idx index in the storage. Used to store a new snapshot.
        '''
        return  self.number() + 1

    def _init(self):
        """
        Initialize the associated storage to allow for trajectory storage

        """
        # define dimensions used in trajectories
        self.storage.createDimension(self.idx_dimension, 0)                 # unlimited number of iterations
