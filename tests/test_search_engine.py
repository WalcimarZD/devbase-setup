
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

from devbase.services.search_engine import SearchEngine

class TestSearchEngine:
    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def mock_embedding_model(self):
        mock = MagicMock()
        # Mock embed to return a generator of dummy vectors
        def mock_embed(documents):
            # Verify documents is a list
            if not isinstance(documents, list):
                print(f"DEBUG: documents is not list: {type(documents)}")
            for _ in documents:
                yield [0.1] * 384
        mock.embed.side_effect = mock_embed
        return mock

    def test_index_file_batches_operations(self, mock_conn, mock_embedding_model, tmp_path):
        """Test that index_file uses batch embedding and executemany."""

        # Setup mocks
        with patch('devbase.services.search_engine.get_connection', return_value=mock_conn), \
             patch('devbase.services.search_engine.TextEmbedding', return_value=mock_embedding_model), \
             patch('devbase.services.search_engine.get_jd_area_for_path', return_value=None), \
             patch('devbase.services.search_engine.sanitize_context') as mock_sanitize:

            engine = SearchEngine()
            # Force mock model
            engine._embedding_model = mock_embedding_model

            # Create dummy content
            num_chunks = 10
            dummy_content = "\n\n".join([f"# Header {i}\nContent for chunk {i}." for i in range(num_chunks)])

            # Setup sanitize return value
            mock_sanitized_obj = MagicMock()
            mock_sanitized_obj.content = dummy_content
            mock_sanitize.return_value = mock_sanitized_obj

            # Create a real temporary file
            test_file = tmp_path / "test_note.md"
            test_file.write_text(dummy_content, encoding="utf-8")

            # Run indexing
            engine.index_file(test_file, force=True)

            # Verify sanitize called
            mock_sanitize.assert_called_once()
            args, _ = mock_sanitize.call_args
            assert args[0] == dummy_content

            # Verify batch embedding was called
            # We expect embed to be called once with a list of all chunks
            assert mock_embedding_model.embed.call_count == 1
            call_args = mock_embedding_model.embed.call_args[0][0]
            assert isinstance(call_args, list)
            assert len(call_args) == num_chunks

            # Verify executemany was called for chunks
            assert mock_conn.executemany.call_count == 1
            call_args = mock_conn.executemany.call_args
            args = call_args[0]

            sql = args[0]
            data_list = args[1]

            assert "INSERT INTO hot_embeddings" in sql
            assert len(data_list) == num_chunks

            # Verify structure of inserted data
            first_row = data_list[0]
            assert first_row[0] == str(test_file)
            assert first_row[1] == 0 # chunk_id
            assert "Content for chunk 0" in first_row[2]
            assert isinstance(first_row[3], list) # embedding
