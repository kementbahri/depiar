import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Paper,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { Edit as EditIcon, Save as SaveIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

interface NotificationPage {
  id: number;
  type: string;
  title: string;
  content: string;
  is_active: boolean;
}

const NotificationPages: React.FC = () => {
  const [pages, setPages] = useState<NotificationPage[]>([]);
  const [selectedPage, setSelectedPage] = useState<NotificationPage | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await axios.get('/api/notifications');
      setPages(response.data);
    } catch (error) {
      enqueueSnackbar('Bildirim sayfaları yüklenirken hata oluştu', { variant: 'error' });
    }
  };

  const handleEdit = (page: NotificationPage) => {
    setSelectedPage(page);
    setEditedContent(page.content);
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    if (!selectedPage) return;

    try {
      await axios.put(`/api/notifications/${selectedPage.type}`, {
        type: selectedPage.type,
        title: selectedPage.title,
        content: editedContent,
      });

      enqueueSnackbar('Bildirim sayfası güncellendi', { variant: 'success' });
      setEditDialogOpen(false);
      fetchPages();
    } catch (error) {
      enqueueSnackbar('Güncelleme sırasında hata oluştu', { variant: 'error' });
    }
  };

  const handleToggle = async (page: NotificationPage) => {
    try {
      await axios.patch(`/api/notifications/${page.type}/toggle`, null, {
        params: { is_active: !page.is_active },
      });

      enqueueSnackbar('Durum güncellendi', { variant: 'success' });
      fetchPages();
    } catch (error) {
      enqueueSnackbar('Durum güncellenirken hata oluştu', { variant: 'error' });
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Bildirim Sayfaları
      </Typography>

      <Grid container spacing={3}>
        {pages.map((page) => (
          <Grid item xs={12} key={page.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">{page.title}</Typography>
                  <Box>
                    <Switch
                      checked={page.is_active}
                      onChange={() => handleToggle(page)}
                      color="primary"
                    />
                    <IconButton onClick={() => handleEdit(page)} color="primary">
                      <EditIcon />
                    </IconButton>
                  </Box>
                </Box>
                <Typography variant="body2" color="textSecondary">
                  Tip: {page.type}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedPage?.title} Düzenle
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={20}
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            variant="outlined"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>İptal</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
          >
            Kaydet
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default NotificationPages; 