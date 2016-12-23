import theano as th
import theano.tensor as tt
from g3py.functions.hypers import Hypers


class Mean(Hypers):
    def __init__(self, call=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if call is not None:
            self.__call__ = call

    def __call__(self, x):
        pass

    def __mul__(self, other):
        if issubclass(type(other), Mean):
            return MeanProd(self, other)
        else:
            return MeanScale(self, other)
    __imul__ = __mul__
    __rmul__ = __mul__

    def __add__(self, other):
        if issubclass(type(other), Mean):
            return MeanSum(self, other)
        else:
            return MeanShift(self, other)
    __iadd__ = __add__
    __radd__ = __add__


class MeanOperation(Mean):
    def __init__(self, _m: Mean, _element):
        self.m = _m
        self.element = _element
        self.hypers = []

    def check_hypers(self, parent=''):
        self.m.check_hypers(parent=parent)
        self.hypers = self.m.hypers

    def default_hypers(self, x=None, y=None):
        return self.m.default_hypers(x, y)

    def __str__(self):
        return str(self.element) + " op " + str(self.m)


class MeanComposition(Mean):
    def __init__(self, _m1: Mean, _m2: Mean):
        self.m1 = _m1
        self.m2 = _m2

    def check_hypers(self, parent=''):
        self.m1.check_hypers(parent=parent)
        self.m2.check_hypers(parent=parent)
        self.hypers = self.m1.hypers + self.m2.hypers

    def default_hypers(self, x=None, y=None):
        return {**self.m1.default_hypers(x, y), **self.m2.default_hypers(x, y)}

    def __str__(self):
        return str(self.m) + " op " + str(self.m)


class MeanScale(MeanOperation):
    def __call__(self, x):
        return self.element * self.m(x)

    def __str__(self):
        return str(self.element) + " * " + str(self.k)


class MeanShift(MeanOperation):
    def __call__(self, x):
        return self.element + self.m(x)

    def __str__(self):
        return str(self.element) + " * " + str(self.k)


class MeanProd(MeanComposition):
    def __call__(self, x):
        return self.m1(x) * self.m2(x)

    def __str__(self):
        return str(self.m1) + " * " + str(self.m2)


class MeanSum(MeanComposition):
    def __call__(self, x):
        return self.m1(x) + self.m2(x)

    def __str__(self):
        return str(self.m1) + " * " + str(self.m2)


class Zero(Mean):
    def __call__(self, x):
        return 0.0


class Bias(Mean):
    def __init__(self, x=None, name=None, constant=None):
        super().__init__(x, name)
        self.constant = constant

    def check_hypers(self, parent=''):
        if self.constant is None:
            self.constant = Hypers.Flat(parent+self.name+'_Constant')
        self.hypers += [self.constant]

    def default_hypers(self, x=None, y=None):
        return {self.constant: y.mean().astype(th.config.floatX)}

    def __call__(self, x):
        return x*0 + self.constant


class Linear(Mean):
    def __init__(self, x=None, name=None, constant=None, coeff=None):
        super().__init__(x, name)
        self.constant = constant
        self.coeff = coeff

    def check_hypers(self, parent=''):
        if self.constant is None:
            self.constant = Hypers.Flat(parent+self.name+'_Constant')
        if self.coeff is None:
            self.coeff = Hypers.Flat(parent+self.name+'_Coeff', shape=self.shape)
        self.hypers += [self.constant, self.coeff]

    def default_hypers(self, x=None, y=None):
        return {self.constant: y.mean().astype(th.config.floatX),
                self.coeff: y.mean()/x.mean()}

    def __call__(self, x):
        return self.constant + tt.dot(x, self.coeff)


