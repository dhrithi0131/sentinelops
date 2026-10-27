from dataclasses import dataclass

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.vector_store import InMemoryVectorStore, VectorMatch
from models.incident import Incident


@dataclass
class IndexedIncident:
    """
    Metadata describing an incident stored in the vector index.
    """

    incident_id: str
    document: str


class IncidentVectorIndex:
    """
    Semantic index for historical incidents.

    Coordinates incident embedding generation and vector storage
    while keeping the incident domain model independent of the
    underlying vector-store implementation.
    """

    def __init__(
        self,
        embedding_service: IncidentEmbeddingService,
        vector_store: InMemoryVectorStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def add_incident(
        self,
        incident: Incident,
    ) -> IndexedIncident:
        """
        Generate an embedding for an incident and store it.

        If the incident already exists, its vector and metadata are
        replaced with the latest incident representation.
        """

        embedded = self.embedding_service.embed_incident(
            incident
        )

        metadata = {
            "incident_id": embedded.incident_id,
            "document": embedded.document,
            **incident.metadata,
        }

        self.vector_store.add(
            record_id=embedded.incident_id,
            vector=embedded.vector,
            metadata=metadata,
        )

        return IndexedIncident(
            incident_id=embedded.incident_id,
            document=embedded.document,
        )

    def update_incident(
        self,
        incident: Incident,
    ) -> IndexedIncident:
        """
        Re-embed an existing incident using its latest state.

        The incident ID remains the stable vector-store key, so the
        previous representation is replaced rather than duplicated.
        """

        return self.add_incident(incident)

    def add_incidents(
        self,
        incidents: list[Incident],
    ) -> list[IndexedIncident]:
        """
        Generate embeddings and index multiple incidents.
        """

        if not incidents:
            return []

        embedded_incidents = (
            self.embedding_service.embed_incidents(
                incidents
            )
        )

        indexed: list[IndexedIncident] = []

        for incident, embedded in zip(incidents, embedded_incidents):
            metadata = {
                "incident_id": embedded.incident_id,
                "document": embedded.document,
                **incident.metadata,
            }

            self.vector_store.add(
                record_id=embedded.incident_id,
                vector=embedded.vector,
                metadata=metadata,
            )

            indexed.append(
                IndexedIncident(
                    incident_id=embedded.incident_id,
                    document=embedded.document,
                )
            )

        return indexed

    
    def search_similar(
        self,
        incident: Incident,
        top_k: int = 5,
    ) -> list[VectorMatch]:
        """
        Retrieve similar incidents, excluding the query incident itself.
        """

        embedded = self.embedding_service.embed_incident(incident)

        # Request one extra result because the query incident may
        # appear in the index and will be filtered out.
        matches = self.vector_store.search(
            query_vector=embedded.vector,
            top_k=top_k + 1,
        )

        return [
            match
            for match in matches
            if match.record_id != incident.id
        ][:top_k]


    def count(self) -> int:
        """Return the number of indexed incidents."""

        return self.vector_store.count()

    def clear(self) -> None:
        """Remove all indexed incidents."""

        self.vector_store.clear()
