from django.db import models
import json

#
#
#
class JSONField(models.TextField) :
    __metaclass__ = models.SubfieldBase

    #def formfield(self, **kwargs) :
    #    pass

    def to_python(self, value) :
        if isinstance(value, basestring) :
            value = json.loads(value)
        if value is None :
            return {}
        return value

    def get_db_prep_save(self, value) :
        if value is None : return
        return json.dumps(value)

    def value_to_string(self, obj) :
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)
