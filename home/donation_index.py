from django_elasticsearch_dsl import DocType, Index, fields
from.models import Donation

donation_index = Index('donation')
donation_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@donation_index.doc_type
class DonationDocument(DocType):
    class Meta:
        model = Donation
        fields = [
            'id',
            'other_products',
            'user__username',
            'user__first_name',
            'donor__location',
        ]

    def get_instances_from_related(self, related_instance):
        return related_instance.donation_set.all()